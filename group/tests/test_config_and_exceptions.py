"""
Extra coverage tests for config and exception handlers.

These are small, focused tests that exercise branches not hit by
the higher‑level tests (e.g. DATABASE_URL fallback, error handlers).
"""

import os
import types
import pytest
from fastapi import Request
from starlette.datastructures import Headers


def make_fake_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": Headers({}).raw,
    }
    return Request(scope)


class TestConfigCoverageExtra:
    def test_get_database_url_prefers_env_DATABASE_URL(self, monkeypatch):
        from app.config import Config

        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/dbname")
        # Clear POSTGRES_* to be sure fallback path is not used
        for var in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_PORT"]:
            monkeypatch.delenv(var, raising=False)

        url = Config.get_database_url()
        assert url == "postgresql://user:pass@host:5432/dbname"

    def test_get_database_url_builds_from_POSTGRES_vars(self, monkeypatch):
        from app.config import Config

        # Clear DATABASE_URL and override the class-level POSTGRES_* attributes
        monkeypatch.delenv("DATABASE_URL", raising=False)
        Config.POSTGRES_USER = "u"
        Config.POSTGRES_PASSWORD = "p"
        Config.POSTGRES_HOST = "h"
        Config.POSTGRES_DB = "d"
        Config.POSTGRES_PORT = "9999"

        url = Config.get_database_url()
        assert url == "postgresql://u:p@h:9999/d"


class TestExceptionHandlersCoverageExtra:
    @pytest.mark.asyncio
    async def test_database_exception_handler_returns_500(self, caplog):
        from app.utils.exceptions import database_exception_handler
        from sqlalchemy.exc import SQLAlchemyError

        request = make_fake_request()
        exc = SQLAlchemyError("db error")

        response = await database_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "DATABASE_ERROR" in body
        # logger.error should have been called; we just ensure something was logged
        assert any("Database error" in message for message in caplog.text.splitlines())

    @pytest.mark.asyncio
    async def test_generic_exception_handler_returns_500(self, caplog):
        from app.utils.exceptions import generic_exception_handler

        request = make_fake_request()
        exc = RuntimeError("boom")

        response = await generic_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "INTERNAL_ERROR" in body
        assert any("Unexpected error" in message for message in caplog.text.splitlines())


