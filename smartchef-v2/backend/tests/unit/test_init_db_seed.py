"""Unit tests for seed permission defaults."""

from app.scripts.init_db import PERMISSIONS, ROLES


def test_seed_permissions_include_batch_test_execute():
    keys = [key for key, _, _ in PERMISSIONS]
    assert "batch_test_execute" in keys


def test_roles_with_batch_test_write_also_get_batch_test_execute():
    for role_name in ("pm", "tester"):
        permissions = ROLES[role_name]["permissions"]
        assert "batch_test_write" in permissions
        assert "batch_test_execute" in permissions
