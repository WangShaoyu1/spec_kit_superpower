"""T006: JWT generation/verification and password hashing unit tests.

Tests for app.core.security module — written before implementation (TDD Red phase).
"""

import pytest


class TestPasswordHashing:
    def test_hash_returns_bcrypt_format(self):
        from app.core.security import hash_password

        result = hash_password("Valid1234")
        assert result.startswith("$2b$")

    def test_verify_correct_password(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("Valid1234")
        assert verify_password("Valid1234", hashed) is True

    def test_verify_wrong_password(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("Valid1234")
        assert verify_password("WrongPass1", hashed) is False

    def test_password_too_short_raises(self):
        from app.core.security import validate_password_strength

        with pytest.raises(Exception):
            validate_password_strength("short1")

    def test_password_no_digit_raises(self):
        from app.core.security import validate_password_strength

        with pytest.raises(Exception):
            validate_password_strength("nonnumeric")

    def test_password_no_letter_raises(self):
        from app.core.security import validate_password_strength

        with pytest.raises(Exception):
            validate_password_strength("12345678")

    def test_valid_password_passes(self):
        from app.core.security import validate_password_strength

        validate_password_strength("Valid1234")


class TestJWT:
    def test_generate_tokens_returns_expected_keys(self):
        from app.core.security import generate_tokens
        from unittest.mock import MagicMock

        user = MagicMock()
        user.id = "test-user-id"
        user.role_id = "test-role-id"
        permissions = [MagicMock(key="intent_library_read")]

        result = generate_tokens(user, permissions)
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "Bearer"
        assert isinstance(result["expires_in"], int)

    @pytest.mark.asyncio
    async def test_verify_valid_access_token(self):
        from app.core.security import generate_tokens, verify_access_token
        from unittest.mock import MagicMock

        user = MagicMock()
        user.id = "test-user-id"
        user.role_id = "test-role-id"
        permissions = [MagicMock(key="intent_library_read")]

        tokens = generate_tokens(user, permissions)
        payload = await verify_access_token(tokens["access_token"])

        assert payload["sub"] == "test-user-id"
        assert payload["role_id"] == "test-role-id"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "intent_library_read" in payload["capabilities"]

    @pytest.mark.asyncio
    async def test_verify_expired_token_raises(self):
        from app.core.security import verify_access_token

        expired = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxMDAwMDAwMDAwfQ."
            "invalid_sig"
        )
        with pytest.raises(Exception):
            await verify_access_token(expired)

    @pytest.mark.asyncio
    async def test_verify_invalid_token_raises(self):
        from app.core.security import verify_access_token

        with pytest.raises(Exception):
            await verify_access_token("not.a.valid.jwt")
