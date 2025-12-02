"""
Additional unit-style tests for `app.routers.chat.websocket_chat`.

On ne teste pas ici le vrai protocole réseau, mais les branches
de validation et d'erreur en mockant `verify_token_ws`, la session DB
et un WebSocket factice.
"""

from uuid import uuid4
from types import SimpleNamespace

import pytest


class FakeWebSocket:
    def __init__(self, messages=None):
        # messages est une liste de payloads texte à renvoyer
        self._messages = list(messages or [])
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None

    async def accept(self):
        self.accepted = True

    async def close(self, code=None, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    async def receive_text(self):
        if self._messages:
            return self._messages.pop(0)
        # Simule une déconnexion quand il n'y a plus de message
        from fastapi import WebSocketDisconnect

        raise WebSocketDisconnect()

    async def send_json(self, data):
        # On n'a pas besoin d'enregistrer pour ces tests,
        # mais on pourrait le faire si nécessaire.
        return


def make_mock_user():
    from datetime import datetime
    from uuid import uuid4

    uid = uuid4()
    return SimpleNamespace(
        id=uid,
        keycloak_id=str(uid),
        email="user@example.com",
        first_name="Test",
        last_name="User",
        is_banned=False,
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_websocket_closes_when_user_profile_missing(monkeypatch):
    """Si l'utilisateur n'existe pas en DB → close WS avec WS_1008 et raison explicite."""
    from app.routers.chat import websocket_chat
    from app.db import get_db, Group, GroupMember, Message
    from app.db.models import User
    from app.middleware import verify_token_ws
    from app.main import app
    from fastapi import status

    fake_ws = FakeWebSocket()
    group_id = uuid4()

    # Token valide avec un sub arbitraire
    async def fake_verify_token_ws(token: str):
        return {"sub": "kc-id", "email": "user@example.com"}

    # DB: aucun user pour ce keycloak_id
    def override_get_db():
        from unittest.mock import MagicMock

        db = MagicMock()

        def query(model):
            if model is User:
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: None))
            return SimpleNamespace()

        db.query = query
        db.__enter__ = lambda s: db
        db.__exit__ = lambda s, *a: False
        return db

    monkeypatch.setattr("app.routers.chat.verify_token_ws", fake_verify_token_ws)
    app.dependency_overrides[get_db] = override_get_db

    try:
        await websocket_chat(fake_ws, group_id, token="token", db=override_get_db())
        assert fake_ws.closed is True
        assert fake_ws.close_code == status.WS_1008_POLICY_VIOLATION
        assert fake_ws.close_reason == "User profile not found"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_closes_when_group_missing(monkeypatch):
    """User existe mais group_id inexistant → fermeture avec 'Group not found'."""
    from app.routers.chat import websocket_chat
    from app.db import get_db, Group
    from app.db.models import User
    from app.middleware import verify_token_ws
    from app.main import app
    from fastapi import status

    fake_ws = FakeWebSocket()
    group_id = uuid4()
    mock_user = make_mock_user()

    async def fake_verify_token_ws(token: str):
        return {"sub": mock_user.keycloak_id, "email": mock_user.email}

    def override_get_db():
        from unittest.mock import MagicMock

        db = MagicMock()

        def query(model):
            if model is User:
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: mock_user))
            if model is Group:
                # Pas de groupe trouvé
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: None))
            return SimpleNamespace()

        db.query = query
        db.__enter__ = lambda s: db
        db.__exit__ = lambda s, *a: False
        return db

    monkeypatch.setattr("app.routers.chat.verify_token_ws", fake_verify_token_ws)
    app.dependency_overrides[get_db] = override_get_db

    try:
        await websocket_chat(fake_ws, group_id, token="token", db=override_get_db())
        assert fake_ws.closed is True
        assert fake_ws.close_code == status.WS_1008_POLICY_VIOLATION
        assert fake_ws.close_reason == "Group not found"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_closes_when_not_member(monkeypatch):
    """User et groupe existent mais l'utilisateur n'est pas membre → 'Not a group member'."""
    from app.routers.chat import websocket_chat
    from app.db import get_db, Group, GroupMember
    from app.db.models import User
    from app.middleware import verify_token_ws
    from app.main import app
    from fastapi import status

    fake_ws = FakeWebSocket()
    group_id = uuid4()
    mock_user = make_mock_user()
    mock_group = SimpleNamespace(id=group_id)

    async def fake_verify_token_ws(token: str):
        return {"sub": mock_user.keycloak_id, "email": mock_user.email}

    def override_get_db():
        from unittest.mock import MagicMock

        db = MagicMock()

        def query(model):
            if model is User:
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: mock_user))
            if model is Group:
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: mock_group))
            if model is GroupMember:
                # Pas d'entrée de membership
                return SimpleNamespace(
                    filter=lambda *_: SimpleNamespace(first=lambda: None)
                )
            return SimpleNamespace()

        db.query = query
        db.__enter__ = lambda s: db
        db.__exit__ = lambda s, *a: False
        return db

    monkeypatch.setattr("app.routers.chat.verify_token_ws", fake_verify_token_ws)
    app.dependency_overrides[get_db] = override_get_db

    try:
        await websocket_chat(fake_ws, group_id, token="token", db=override_get_db())
        assert fake_ws.closed is True
        assert fake_ws.close_code == status.WS_1008_POLICY_VIOLATION
        assert fake_ws.close_reason == "Not a group member"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_invalid_json_triggers_parse_error(monkeypatch):
    """
    Quand un message texte n'est pas du JSON valide,
    le handler doit utiliser chat_manager.send_error avec PARSE_ERROR.
    """
    from app.routers.chat import websocket_chat
    from app.db import get_db, Group, GroupMember
    from app.db.models import User
    from app.middleware import verify_token_ws
    from app.main import app

    # Un seul message qui n'est pas du JSON, puis WebSocketDisconnect
    fake_ws = FakeWebSocket(messages=["not-json"])
    group_id = uuid4()
    mock_user = make_mock_user()
    mock_group = SimpleNamespace(id=group_id)
    mock_member = SimpleNamespace(user_id=mock_user.id, group_id=group_id)

    async def fake_verify_token_ws(token: str):
        return {"sub": mock_user.keycloak_id, "email": mock_user.email}

    def override_get_db():
        from unittest.mock import MagicMock

        db = MagicMock()

        def query(model):
            if model is User:
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: mock_user))
            if model is Group:
                return SimpleNamespace(filter=lambda *_: SimpleNamespace(first=lambda: mock_group))
            if model is GroupMember:
                return SimpleNamespace(
                    filter=lambda *_: SimpleNamespace(first=lambda: mock_member)
                )
            return SimpleNamespace()

        db.query = query
        db.__enter__ = lambda s: db
        db.__exit__ = lambda s, *a: False
        return db

    # Faux chat_manager pour capter l'erreur
    class FakeChatManager:
        def __init__(self):
            self.errors = []

        async def connect(self, *_, **__):
            return

        async def send_error(self, websocket, code: str, message: str):
            self.errors.append((code, message))

        async def disconnect(self, *_, **__):
            return

    fake_manager = FakeChatManager()

    monkeypatch.setattr("app.routers.chat.verify_token_ws", fake_verify_token_ws)
    monkeypatch.setattr("app.routers.chat.chat_manager", fake_manager)
    app.dependency_overrides[get_db] = override_get_db

    try:
        await websocket_chat(fake_ws, group_id, token="token", db=override_get_db())
        # On doit avoir reçu au moins une erreur PARSE_ERROR
        assert any(code == "PARSE_ERROR" for code, _ in fake_manager.errors)
    finally:
        app.dependency_overrides.clear()


