"""Tests for custom exception handlers."""
import pytest
from unittest.mock import MagicMock
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation exception handler formats errors correctly."""
        from app.utils.exceptions import validation_exception_handler

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        # Create a validation error with mock errors
        mock_errors = [
            {
                "loc": ("body", "name"),
                "msg": "field required",
                "type": "value_error.missing"
            },
            {
                "loc": ("body", "event_start"),
                "msg": "invalid datetime",
                "type": "type_error.datetime"
            }
        ]

        # Create RequestValidationError with mock errors
        exc = RequestValidationError(errors=mock_errors)

        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == 422
        # Check response body structure
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Invalid request data"
        assert len(body["error"]["details"]) == 2
        assert body["error"]["details"][0]["field"] == "body.name"
        assert body["error"]["details"][0]["message"] == "field required"


class TestDatabaseExceptionHandler:
    """Tests for database_exception_handler."""

    @pytest.mark.asyncio
    async def test_database_exception_handler(self):
        """Test database exception handler returns 500 with proper format."""
        from app.utils.exceptions import database_exception_handler

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        # Create a SQLAlchemy error
        exc = SQLAlchemyError("Connection refused")

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "DATABASE_ERROR"
        assert body["error"]["message"] == "An internal database error occurred"


class TestGenericExceptionHandler:
    """Tests for generic_exception_handler."""

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """Test generic exception handler returns 500 with proper format."""
        from app.utils.exceptions import generic_exception_handler

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        # Create a generic exception
        exc = Exception("Something went wrong")

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "An unexpected error occurred"

    @pytest.mark.asyncio
    async def test_generic_exception_handler_with_custom_exception(self):
        """Test generic exception handler with a custom exception type."""
        from app.utils.exceptions import generic_exception_handler

        mock_request = MagicMock(spec=Request)

        # Custom exception
        class CustomError(Exception):
            pass

        exc = CustomError("Custom error message")

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "INTERNAL_ERROR"
