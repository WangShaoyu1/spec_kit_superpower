"""T008: Unified API response envelope + error code format unit tests.

Tests for app.core.api_response module.
Written before implementation (TDD Red phase).
"""

import pytest


class TestSuccessResponse:
    def test_default_success(self):
        from app.core.api_response import success_response

        resp = success_response({"key": "value"})
        body = resp.body
        import json
        data = json.loads(body)
        assert data["code"] == "000000"
        assert data["data"] == {"key": "value"}
        assert data["msg"] == "success"
        assert resp.status_code == 200

    def test_custom_message(self):
        from app.core.api_response import success_response

        resp = success_response({"id": 1}, msg="created")
        import json
        data = json.loads(resp.body)
        assert data["msg"] == "created"

    def test_null_data(self):
        from app.core.api_response import success_response

        resp = success_response(None)
        import json
        data = json.loads(resp.body)
        assert data["data"] is None

    def test_custom_status_code(self):
        from app.core.api_response import success_response

        resp = success_response({"id": 1}, status_code=201)
        assert resp.status_code == 201


class TestErrorResponse:
    def test_error_401(self):
        from app.core.api_response import error_response

        resp = error_response("E10101", "用户名或密码错误", 401)
        import json
        data = json.loads(resp.body)
        assert data["code"] == "E10101"
        assert data["data"] is None
        assert data["msg"] == "用户名或密码错误"
        assert resp.status_code == 401

    def test_error_403(self):
        from app.core.api_response import error_response

        resp = error_response("E10107", "无权限执行此操作", 403)
        import json
        data = json.loads(resp.body)
        assert resp.status_code == 403
        assert data["code"] == "E10107"

    def test_error_422(self):
        from app.core.api_response import error_response

        resp = error_response("E10205", "密码至少 8 位", 422)
        assert resp.status_code == 422


class TestPaginatedResponse:
    def test_paginated(self):
        from app.core.api_response import paginated_response

        items = [{"id": i} for i in range(10)]
        resp = paginated_response(items, total=50, page=1, page_size=10)
        import json
        data = json.loads(resp.body)
        assert data["code"] == "000000"
        assert data["data"]["items"] == items
        assert data["data"]["total"] == 50
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 10
        assert data["data"]["pages"] == 5

    def test_paginated_partial_page(self):
        from app.core.api_response import paginated_response

        resp = paginated_response([], total=0, page=1, page_size=20)
        import json
        data = json.loads(resp.body)
        assert data["data"]["pages"] == 0
        assert data["data"]["items"] == []
