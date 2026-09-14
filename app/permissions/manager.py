from __future__ import annotations

from enum import IntEnum


class PermissionLevel(IntEnum):
    READ = 1
    SAFE_WRITE = 2
    EXECUTE = 3
    DESTRUCTIVE = 4


class PermissionManager:
    """Manage the permissions available to Genos."""

    def __init__(self):
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
