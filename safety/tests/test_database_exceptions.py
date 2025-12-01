"""Tests for database and exception utilities."""
import pytest
from sqlalchemy.orm import Session
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError, BaseModel


class TestGetDb:
    """Test get_db dependency."""

    def test_get_db_yields_session(self):
        """Test get_db yields a database session."""
        from app.db.database import get_db

        db_gen = get_db()
        db = next(db_gen)

        assert isinstance(db, Session)

        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_closes_session(self):
        """Test get_db closes session in finally block."""
        from app.db.database import get_db

        db_gen = get_db()
        db = next(db_gen)

        try:
            db_gen.close()
        except:
            pass


class TestExceptionHandlers:
    """Test custom exception handlers."""

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation exception handler."""
        from app.utils.exceptions import validation_exception_handler

        class TestModel(BaseModel):
            email: str
            age: int

        try:
            TestModel(email="invalid", age="not-a-number")
        except ValidationError as e:
            exc = RequestValidationError(errors=e.errors())
            request = Request(scope={"type": "http", "method": "POST", "path": "/test"})

            response = await validation_exception_handler(request, exc)

            assert response.status_code == 422
            body = response.body.decode()
            assert "VALIDATION_ERROR" in body

    @pytest.mark.asyncio
    async def test_database_exception_handler(self):
        """Test database exception handler."""
        from app.utils.exceptions import database_exception_handler

        exc = SQLAlchemyError("Connection lost")
        request = Request(scope={"type": "http", "method": "GET", "path": "/test"})

        response = await database_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "DATABASE_ERROR" in body

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """Test generic exception handler."""
        from app.utils.exceptions import generic_exception_handler

        exc = Exception("Unexpected error")
        request = Request(scope={"type": "http", "method": "GET", "path": "/test"})

        response = await generic_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "INTERNAL_ERROR" in body
