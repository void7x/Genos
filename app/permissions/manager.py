from __future__ import annotations

from enum import IntEnum


class PermissionLevel(IntEnum):
    READ = 1
    SAFE_WRITE = 2
    EXECUTE = 3
    DESTRUCTIVE = 4


class PermissionManager:
    """Manage permissions for the currently active Genos workspace."""

    def __init__(self):
        self._granted = {PermissionLevel.READ}
        self._workspace_key: str | None = None

    def bind_workspace(self, workspace_key: str) -> None:
        key = str(workspace_key).strip()
        if not key:
            raise ValueError("Workspace key cannot be empty.")

        # First workspace binding preserves permissions that were already
        # explicitly granted.
        if self._workspace_key is None:
            self._workspace_key = key
            return

        # Rebinding to the same workspace does nothing.
        if self._workspace_key == key:
            return

        # Switching workspaces is a security boundary.
        self._workspace_key = key
        self._granted = {PermissionLevel.READ}

    def grant(self, permission: PermissionLevel) -> None:
        self._granted.add(permission)

    def revoke(self, permission: PermissionLevel) -> None:
        if permission == PermissionLevel.READ:
            return

        self._granted.discard(permission)

    def is_allowed(self, permission: PermissionLevel) -> bool:
        return permission in self._granted

    def require(self, permission: PermissionLevel) -> None:
        if not self.is_allowed(permission):
            raise PermissionError(
                f"Permission denied: {permission.name}"
            )

    def granted(self) -> set[PermissionLevel]:
        return set(self._granted)
