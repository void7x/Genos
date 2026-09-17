from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import threading
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from app.agent.workflow import PendingAction
from app.chat.runtime import GenosRuntime
from app.permissions import PermissionLevel

MAX_BODY_BYTES = 64 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787

ALLOWED_ORIGINS = {
    "http://127.0.0.1:5178",
    "http://localhost:5178",
    "http://127.0.0.1:4178",
    "http://localhost:4178",
}

COMMANDS = {
    "sendMessage",
    "approveAction",
    "denyAction",
    "resumeWorkflow",
    "retryWorkflow",
    "requestRollback",
    "dismissNotification",
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class GenosApi:
    """Small, local-only HTTP adapter around the existing Genos runtime."""

    def __init__(self, workspace: str | Path, data_root: str | Path | None = None):
        self._lock = threading.RLock()
        self.runtime = GenosRuntime(workspace, data_root=data_root)

    def state(self) -> dict[str, Any]:
        with self._lock:
            runtime = self.runtime
            info = runtime.inspector.inspect(runtime.root)
            git = _git_snapshot(runtime.root)
            tasks = runtime.tasks.list(runtime.workspace.id)
            goals = runtime.goals.list(runtime.workspace.id)
            memories = runtime.memory.list(runtime.workspace.id)
            history = runtime.history.list(runtime.workspace.id)
            conversation = runtime.conversation.load()
            pending = runtime.workflow.pending
            multi_step = runtime.multi_step.pending

            messages = []
            for index, item in enumerate(conversation[-100:]):
                role = "user" if item.get("role") == "user" else "genos"
                content = str(item.get("content", "")).strip()
                if not content:
                    continue
                digest = hashlib.sha1(
                    f"{index}:{role}:{content}".encode("utf-8")
                ).hexdigest()[:16]
                messages.append(
                    {
                        "id": f"msg_{digest}",
                        "role": role,
                        "blocks": [{"kind": "text", "text": content}],
                        "at": datetime.now(timezone.utc).isoformat(),
                    }
                )

            workflow = _workflow_snapshot(runtime.workspace.id, pending, multi_step)
            permission = _permission_request(pending)
            latest = history[-1] if history else None
            verification = _verification_from_history(latest)
            recovery = _recovery_from_history(latest)
            rollback = _rollback_from_history(latest)

            goal = _goal_snapshot(goals, tasks)
            files = _relevant_files(pending, multi_step, history)

            if permission is not None:
                status = "waiting"
                status_detail = f"Approval required: {permission['target']}"
            elif latest is not None and latest.verification.casefold() == "failed":
                status = "error"
                status_detail = latest.summary or "Verification failed"
            elif latest is not None and latest.status.casefold() == "success":
                status = "success"
                status_detail = latest.summary or "Completed"
            else:
                status = "idle"
                status_detail = "Ready"

            return {
                "project": {
                    "id": runtime.workspace.id,
                    "name": runtime.workspace.name,
                    "path": str(runtime.root),
                    "language": info.languages[0] if info.languages else "Unknown",
                    "branch": git["branch"],
                    "gitState": git,
                    "tests": _test_summary_from_history(history),
                    "workspace": runtime.workspace.name,
                },
                "status": status,
                "statusDetail": status_detail,
                "messages": messages,
                "workflow": workflow,
                "permission": permission,
                "verification": verification,
                "recovery": recovery,
                "rollback": rollback,
                "memories": [
                    {
                        "id": memory.id,
                        "text": memory.content,
                        "scope": "project",
                        "source": ", ".join(memory.tags) or "Genos memory",
                        "at": memory.updated_at,
                    }
                    for memory in memories[-100:]
                ],
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "state": _task_state(task.status),
                    }
                    for task in tasks
                ],
                "goal": goal,
                "history": [
                    {
                        "id": entry.id,
                        "kind": _history_kind(entry.action),
                        "label": f"{entry.action.title()}: {entry.target}",
                        "detail": entry.summary or None,
                        "at": entry.timestamp,
                        "status": _history_status(entry.status, entry.rollback),
                    }
                    for entry in reversed(history[-50:])
                ],
                "files": files,
                "notifications": [],
                "busy": multi_step is not None and multi_step.status == "running",
            }

    def command(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ApiError("invalid-request", "Command body must be a JSON object.")

        command_type = payload.get("type")
        if command_type not in COMMANDS:
            raise ApiError("invalid-request", "Unknown Genos command.")

        with self._lock:
            if command_type == "sendMessage":
                text = _bounded_string(payload.get("text"), 20_000, "Message")
                self.runtime.handle(text)
                return
            if command_type == "approveAction":
                self.runtime.handle("approve")
                return
            if command_type == "denyAction":
                self.runtime.handle("deny")
                return
            if command_type == "resumeWorkflow":
                self.runtime.handle("resume workflow")
                return
            if command_type == "retryWorkflow":
                self._retry_workflow()
                return
            if command_type == "requestRollback":
                raise ApiError(
                    "invalid-request",
                    "The current backend performs rollback automatically after failed edits.",
                )
            if command_type == "dismissNotification":
                _bounded_string(payload.get("id"), 128, "Notification id")
                return

    def _retry_workflow(self) -> None:
        plan = self.runtime.multi_step.pending
        if plan is None:
            raise ApiError("invalid-request", "There is no failed workflow to retry.")
        if plan.status != "failed":
            raise ApiError("conflict", "The current workflow is not in a failed state.")

        reset = type(plan)(
            task_id=plan.task_id,
            title=plan.title,
            steps=plan.steps,
            current_step=1,
            status="pending",
        )
        self.runtime.multi_step.pending = reset
        self.runtime.workflow_state.save(self.runtime.workspace.id, reset)
        self.runtime.multi_step.approve(self.runtime.workspace.id)


def _bounded_string(value: Any, limit: int, label: str) -> str:
    if not isinstance(value, str):
        raise ApiError("invalid-request", f"{label} must be a string.")
    value = value.strip()
    if not value:
        raise ApiError("invalid-request", f"{label} cannot be empty.")
    if len(value) > limit:
        raise ApiError("invalid-request", f"{label} is too long.")
    return value


def _git_snapshot(root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""

    branch = run("branch", "--show-current") or "Not a Git repository"
    porcelain = run("status", "--porcelain")
    last_commit = run("log", "-1", "--pretty=%h %s") or "No commits"
    ahead = behind = 0
    counts = run("rev-list", "--left-right", "--count", "@{upstream}...HEAD")
    if counts:
        try:
            behind_s, ahead_s = counts.split()[:2]
            behind, ahead = int(behind_s), int(ahead_s)
        except (ValueError, IndexError):
            pass
    return {
        "branch": branch,
        "clean": porcelain == "",
        "modifiedFiles": len([line for line in porcelain.splitlines() if line.strip()]),
        "ahead": ahead,
        "behind": behind,
        "lastCommit": last_commit,
    }


def _task_state(status: str) -> str:
    return {
        "completed": "done",
        "in_progress": "active",
        "planned": "todo",
    }.get(status, "todo")


def _history_kind(action: str) -> str:
    action = action.casefold()
    if action in {"write", "edit"}:
        return "edit"
    if action in {"execute", "command"}:
        return "command"
    if action in {"test", "tests"}:
        return "test"
    if action in {"git"}:
        return "git"
    if action in {"task"}:
        return "task"
    if action in {"rollback"}:
        return "rollback"
    if action in {"permission"}:
        return "permission"
    return "inspect"


def _history_status(status: str, rollback: str) -> str:
    if rollback.casefold() == "passed":
        return "undone"
    return "ok" if status.casefold() == "success" else "failed"


def _goal_snapshot(goals, tasks) -> dict[str, Any]:
    active = [goal for goal in goals if goal.status == "active"]
    goal = active[-1] if active else (goals[-1] if goals else None)
    if goal is None:
        return {
            "id": "goal_none",
            "title": "No active goal",
            "progress": 0,
            "detail": "Create a goal before planning a larger task.",
        }
    related = [task for task in tasks if task.goal_title.casefold() == goal.title.casefold()]
    completed = sum(task.status == "completed" for task in related)
    progress = (completed / len(related)) if related else 0
    return {
        "id": goal.title.casefold().replace(" ", "_")[:64],
        "title": goal.title,
        "progress": progress,
        "detail": f"{completed}/{len(related)} linked tasks completed" if related else goal.description or "Active goal",
    }


def _workflow_snapshot(workspace_id: str, pending: PendingAction | None, multi_step) -> dict[str, Any]:
    if multi_step is not None:
        phases = [
            {"stage": "plan", "label": "Plan", "status": "done"},
            {"stage": "approval", "label": "Approval", "status": "active" if multi_step.status == "pending" else "done"},
            {"stage": "execute", "label": "Execute", "status": "active" if multi_step.status == "running" else ("failed" if multi_step.status == "failed" else "pending")},
            {"stage": "verify", "label": "Verify", "status": "pending"},
            {"stage": "recover", "label": "Recover", "status": "pending"},
            {"stage": "complete", "label": "Complete", "status": "done" if multi_step.status == "completed" else "pending"},
        ]
        steps = []
        total = len(multi_step.steps)
        current = max(1, multi_step.current_step)
        for index, step in enumerate(multi_step.steps, 1):
            step_status = "completed" if index < current else ("running" if index == current and multi_step.status == "running" else "waiting" if multi_step.status == "pending" else "failed" if index == current and multi_step.status == "failed" else "pending")
            steps.append({
                "id": f"step_{index}",
                "index": index,
                "title": step.reason or step.action.replace("_", " ").title(),
                "status": step_status,
                "detail": step.target,
                "command": step.target if step.action == "execute" else None,
            })
        completed = sum(step["status"] == "completed" for step in steps)
        return {
            "id": f"workflow_{multi_step.task_id}",
            "name": multi_step.title,
            "phase": "approval" if multi_step.status == "pending" else "execute" if multi_step.status == "running" else "verify" if multi_step.status == "failed" else "complete",
            "phases": phases,
            "steps": steps,
            "progress": (completed / total) if total else 0,
            "persistable": True,
            "resumable": multi_step.status in {"pending", "running"},
            "interrupted": multi_step.status in {"pending", "failed"},
        }
    if pending is not None:
        plan = pending.plan
        return {
            "id": f"workflow_{workspace_id}",
            "name": f"{plan.action.title()} {plan.target}",
            "phase": "approval",
            "phases": [
                {"stage": "plan", "label": "Plan", "status": "done"},
                {"stage": "approval", "label": "Approval", "status": "active"},
                {"stage": "execute", "label": "Execute", "status": "pending"},
                {"stage": "verify", "label": "Verify", "status": "pending"},
                {"stage": "recover", "label": "Recover", "status": "pending"},
                {"stage": "complete", "label": "Complete", "status": "pending"},
            ],
            "steps": [
                {"id": "plan", "index": 1, "title": "Review planned change", "status": "completed", "detail": plan.target},
                {"id": "approval", "index": 2, "title": "Approve action", "status": "waiting"},
                {"id": "execute", "index": 3, "title": f"Execute {plan.action}", "status": "pending", "detail": plan.target, "command": plan.target if plan.action == "execute" else None},
                {"id": "verify", "index": 4, "title": "Verify result", "status": "pending"},
            ],
            "progress": 0.25,
            "persistable": False,
            "resumable": False,
            "interrupted": False,
        }
    return {
        "id": f"workflow_{workspace_id}",
        "name": "No active workflow",
        "phase": "complete",
        "phases": [
            {"stage": stage, "label": stage.title(), "status": "pending" if stage != "complete" else "done"}
            for stage in ("plan", "approval", "execute", "verify", "recover", "complete")
        ],
        "steps": [],
        "progress": 0,
        "persistable": True,
        "resumable": False,
        "interrupted": False,
    }


def _permission_request(pending: PendingAction | None) -> dict[str, Any] | None:
    if pending is None:
        return None
    operation = {
        "write": "write-file",
        "edit": "edit-file",
        "execute": "run-command",
    }.get(pending.plan.action, "edit-file")
    risk = "high" if pending.permission in {PermissionLevel.EXECUTE, PermissionLevel.DESTRUCTIVE} else "medium"
    return {
        "id": f"permission_{pending.plan.target}",
        "operation": operation,
        "target": pending.plan.target,
        "reason": "Genos prepared this action and requires your explicit permission before changing the workspace.",
        "risk": risk,
        "state": "pending",
        "command": pending.plan.target if pending.plan.action == "execute" else None,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


def _verification_from_history(entry) -> dict[str, Any] | None:
    if entry is None or entry.verification.casefold() not in {"passed", "failed"}:
        return None
    passed = entry.verification.casefold() == "passed"
    output = entry.summary or ""
    failed_count = 0 if passed else _failed_count(output)
    return {
        "id": entry.id,
        "passed": passed,
        "checks": [
            {
                "id": "verification",
                "label": "Backend verification",
                "status": "passed" if passed else "failed",
                "detail": entry.summary or None,
            }
        ],
        "summary": entry.summary or ("Verification passed" if passed else "Verification failed"),
        "failure": None if passed else {
            "title": entry.target,
            "detail": entry.summary or "Verification failed",
            "failedCount": failed_count,
            "output": output,
        },
    }


def _failed_count(text: str) -> int:
    match = re.search(r"(\d+)\s+failed", text, re.IGNORECASE)
    return int(match.group(1)) if match else 1


def _recovery_from_history(entry) -> dict[str, Any] | None:
    if entry is None or entry.recovery.casefold() in {"", "not-needed"}:
        return None
    return {
        "active": entry.recovery.casefold() == "in-progress",
        "title": "Recovery",
        "detail": entry.recovery,
        "automatic": True,
        "attempt": 1,
    }


def _rollback_from_history(entry) -> dict[str, Any] | None:
    if entry is None or entry.rollback.casefold() in {"", "not-needed"}:
        return None
    return {
        "active": entry.rollback.casefold() != "passed",
        "target": entry.target,
        "detail": entry.rollback,
        "restored": entry.rollback.casefold() == "passed",
    }


def _test_summary_from_history(history) -> dict[str, Any]:
    latest = next((entry for entry in reversed(history) if "pytest" in entry.target.casefold()), None)
    if latest is None:
        return {"passed": 0, "failed": 0, "skipped": 0, "durationMs": 0, "lastRun": ""}
    summary = latest.summary or ""
    def number(word: str) -> int:
        match = re.search(rf"(\d+)\s+{word}", summary, re.IGNORECASE)
        return int(match.group(1)) if match else 0
    return {
        "passed": number("passed"),
        "failed": number("failed"),
        "skipped": number("skipped"),
        "durationMs": 0,
        "lastRun": latest.timestamp,
    }


def _relevant_files(pending, multi_step, history) -> list[dict[str, Any]]:
    paths: list[tuple[str, str | None]] = []
    if pending is not None:
        paths.append((pending.plan.target, "modified" if pending.plan.action == "edit" else "added"))
    if multi_step is not None:
        for step in multi_step.steps:
            if step.target and step.action in {"edit", "write"}:
                paths.append((step.target, "modified"))
    for entry in reversed(history[-20:]):
        if "/" in entry.target or "\\" in entry.target:
            paths.append((entry.target, "modified"))
    seen = set()
    output = []
    for path, change in paths:
        if path in seen:
            continue
        seen.add(path)
        output.append({"path": path, "change": change})
    return output[:50]


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Unsupported value: {type(value)!r}")


class Handler(BaseHTTPRequestHandler):
    server_version = "GenosLocalAPI/1.0"

    @property
    def api(self) -> GenosApi:
        return self.server.genos_api  # type: ignore[attr-defined]

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        return origin is None or origin in ALLOWED_ORIGINS

    def _send(self, status: int, payload: dict[str, Any], origin: str | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, error: ApiError) -> None:
        origin = self.headers.get("Origin")
        self._send(error.status, {"ok": False, "error": {"code": error.code, "message": error.message}}, origin)

    def do_OPTIONS(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin")
        if not self._origin_ok():
            self._send(403, {"ok": False, "error": {"code": "backend-unavailable", "message": "Origin is not allowed."}})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._origin_ok():
            self._error(ApiError("backend-unavailable", "Origin is not allowed.", 403))
            return
        try:
            if self.path == "/api/v1/health":
                self._send(200, {"ok": True, "service": "genos"}, self.headers.get("Origin"))
                return
            if self.path == "/api/v1/state":
                self._send(200, {"ok": True, "state": self.api.state()}, self.headers.get("Origin"))
                return
            self._send(404, {"ok": False, "error": {"code": "invalid-request", "message": "Unknown endpoint."}}, self.headers.get("Origin"))
        except Exception:
            self._error(ApiError("unknown", "Genos failed to build the current state.", 500))

    def do_POST(self) -> None:  # noqa: N802
        if not self._origin_ok():
            self._error(ApiError("backend-unavailable", "Origin is not allowed.", 403))
            return
        if self.path != "/api/v1/command":
            self._send(404, {"ok": False, "error": {"code": "invalid-request", "message": "Unknown endpoint."}}, self.headers.get("Origin"))
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ApiError("invalid-request", "Request body is missing or too large.")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            self.api.command(payload)
            self._send(200, {"ok": True, "state": self.api.state()}, self.headers.get("Origin"))
        except json.JSONDecodeError:
            self._error(ApiError("invalid-request", "Request body must be valid JSON."))
        except ApiError as error:
            self._error(error)
        except PermissionError as error:
            self._error(ApiError("permission-denied", str(error)))
        except Exception:
            self._error(ApiError("unknown", "Genos could not complete the requested operation.", 500))

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[Genos API] {self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Genos frontend API bridge.")
    parser.add_argument("--workspace", default=os.environ.get("GENOS_WORKSPACE", os.getcwd()))
    parser.add_argument("--data-root", default=os.environ.get("GENOS_DATA_ROOT"))
    parser.add_argument("--host", default=os.environ.get("GENOS_API_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("GENOS_API_PORT", DEFAULT_PORT)))
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("Genos API must bind to loopback during this integration phase.")

    api = GenosApi(args.workspace, args.data_root)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.genos_api = api  # type: ignore[attr-defined]
    print(f"GENOS API listening on http://{args.host}:{args.port}")
    print(f"Workspace: {api.runtime.root}")
    server.serve_forever()


if __name__ == "__main__":
    main()
