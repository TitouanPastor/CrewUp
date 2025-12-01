"""Tests for exception handlers."""
import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError, BaseModel


class TestExceptionHandlers:
    """Test custom exception handlers."""

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation exception handler formats errors correctly."""
        from app.utils.exceptions import validation_exception_handler

        # Create a mock validation error
        class TestModel(BaseModel):
            email: str
            age: int

        try:
            TestModel(email="invalid", age="not-a-number")
        except ValidationError as e:
            # Convert to RequestValidationError
            exc = RequestValidationError(errors=e.errors())

            # Create mock request
            request = Request(scope={"type": "http", "method": "POST", "path": "/test"})

            # Call handler
            response = await validation_exception_handler(request, exc)

            assert response.status_code == 422
            body = response.body.decode()
            assert "VALIDATION_ERROR" in body
            assert "Invalid request data" in body

    @pytest.mark.asyncio
    async def test_database_exception_handler(self):
        """Test database exception handler."""
        from app.utils.exceptions import database_exception_handler

        # Create mock database error
        exc = SQLAlchemyError("Connection lost")

        # Create mock request
        request = Request(scope={"type": "http", "method": "GET", "path": "/test"})

        # Call handler
        response = await database_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "DATABASE_ERROR" in body
        assert "database error occurred" in body

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """Test generic exception handler."""
        from app.utils.exceptions import generic_exception_handler

        # Create generic exception
        exc = Exception("Unexpected error")

        # Create mock request
        request = Request(scope={"type": "http", "method": "GET", "path": "/test"})

        # Call handler
        response = await generic_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "INTERNAL_ERROR" in body
        assert "unexpected error occurred" in body
