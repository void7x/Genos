import pytest

from app.permissions import PermissionLevel, PermissionManager


def test_read_is_allowed_by_default():
    manager = PermissionManager()

    assert manager.is_allowed(PermissionLevel.READ) is True


def test_write_is_denied_by_default():
    manager = PermissionManager()

    assert manager.is_allowed(PermissionLevel.SAFE_WRITE) is False


def test_execute_is_denied_by_default():
    manager = PermissionManager()

    assert manager.is_allowed(PermissionLevel.EXECUTE) is False


def test_destructive_is_denied_by_default():
    manager = PermissionManager()

    assert manager.is_allowed(PermissionLevel.DESTRUCTIVE) is False


def test_grant_permission():
    manager = PermissionManager()

    manager.grant(PermissionLevel.SAFE_WRITE)

    assert manager.is_allowed(PermissionLevel.SAFE_WRITE) is True


def test_revoke_permission():
    manager = PermissionManager()

    manager.grant(PermissionLevel.EXECUTE)
    manager.revoke(PermissionLevel.EXECUTE)

    assert manager.is_allowed(PermissionLevel.EXECUTE) is False


def test_read_cannot_be_revoked():
    manager = PermissionManager()

    manager.revoke(PermissionLevel.READ)

    assert manager.is_allowed(PermissionLevel.READ) is True


def test_require_allows_granted_permission():
    manager = PermissionManager()

    manager.require(PermissionLevel.READ)


def test_require_rejects_denied_permission():
    manager = PermissionManager()

    with pytest.raises(PermissionError, match="Permission denied"):
        manager.require(PermissionLevel.EXECUTE)


def test_granted_returns_copy():
    manager = PermissionManager()

    granted = manager.granted()
    granted.clear()

    assert manager.is_allowed(PermissionLevel.READ) is True


def test_permissions_are_ordered():
    assert PermissionLevel.READ < PermissionLevel.SAFE_WRITE
    assert PermissionLevel.SAFE_WRITE < PermissionLevel.EXECUTE
    assert PermissionLevel.EXECUTE < PermissionLevel.DESTRUCTIVE
