"""
Unit tests for `app.services.chat_manager.ChatManager` and `RateLimiter`.

These tests are pure unit tests (no real WebSocket or DB) and focus on:
- rate limiting behaviour
- connection tracking
- broadcast / system message paths
"""

from uuid import uuid4
from types import SimpleNamespace

import pytest


def make_fake_ws():
    """Create a minimal fake WebSocket object with send_json coroutine."""

    class FakeWS:
        def __init__(self):
            self.sent = []
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_json(self, data):
            self.sent.append(data)

    return FakeWS()


class TestRateLimiter:
    def test_rate_limiter_allows_under_limit(self):
        from app.services.chat_manager import RateLimiter

        rl = RateLimiter(max_messages=3, window_seconds=60)
        user_id = uuid4()

        assert rl.is_allowed(user_id) is True
        assert rl.is_allowed(user_id) is True
        assert rl.is_allowed(user_id) is True

    def test_rate_limiter_blocks_over_limit(self):
        from app.services.chat_manager import RateLimiter

        rl = RateLimiter(max_messages=2, window_seconds=60)
        user_id = uuid4()

        assert rl.is_allowed(user_id) is True
        assert rl.is_allowed(user_id) is True
        # Third call should be blocked
        assert rl.is_allowed(user_id) is False


class TestChatManagerBasics:
    @pytest.mark.asyncio
    async def test_connect_and_disconnect_updates_connection_count(self):
        from app.services.chat_manager import ChatManager

        manager = ChatManager()
        group_id = uuid4()
        user_id = uuid4()

        ws = make_fake_ws()

        # Monkeypatch broadcast_member_event to avoid recursive behaviour
        async def no_broadcast(*args, **kwargs):
            return None

        manager.broadcast_member_event = no_broadcast  # type: ignore

        assert manager.get_connection_count(group_id) == 0

        await manager.connect(group_id, ws, user_id, "tester")
        assert ws.accepted is True
        assert manager.get_connection_count(group_id) == 1

        await manager.disconnect(group_id, ws, user_id, "tester")
        assert manager.get_connection_count(group_id) == 0

    @pytest.mark.asyncio
    async def test_broadcast_message_skips_excluded_and_handles_disconnect(self):
        from app.services.chat_manager import ChatManager

        manager = ChatManager()
        group_id = uuid4()

        ws_sender = make_fake_ws()
        ws_receiver_ok = make_fake_ws()
        ws_receiver_fail = make_fake_ws()

        user_sender = uuid4()
        user_ok = uuid4()
        user_fail = uuid4()

        # Pre-register connections (using str keys and list format)
        manager.connections[str(group_id)] = [
            (ws_sender, str(user_sender), "sender"),
            (ws_receiver_ok, str(user_ok), "ok"),
            (ws_receiver_fail, str(user_fail), "fail"),
        ]

        # Make one receiver raise when sending
        async def failing_send_json(_):
            raise RuntimeError("send failed")

        ws_receiver_fail.send_json = failing_send_json  # type: ignore

        # Simple WSMessageOut stand‑in
        msg = SimpleNamespace(
            model_dump=lambda mode="json": {"type": "message", "content": "hello"}
        )

        # Monkeypatch disconnect to avoid recursive broadcast
        async def fake_disconnect(group_id_arg, ws_arg, user_id_arg, username_arg):
            # Ensure it's called for the failing connection
            assert group_id_arg == group_id
            assert ws_arg is ws_receiver_fail

        manager.disconnect = fake_disconnect  # type: ignore

        await manager.broadcast_message(group_id, msg, exclude_websocket=ws_sender)

        # Sender should not receive anything
        assert ws_sender.sent == []
        # OK receiver should have exactly one message
        assert ws_receiver_ok.sent == [{"type": "message", "content": "hello"}]

    @pytest.mark.asyncio
    async def test_broadcast_system_message_counts_successes(self):
        from app.services.chat_manager import ChatManager

        manager = ChatManager()
        group_id = uuid4()

        ws1 = make_fake_ws()
        ws2 = make_fake_ws()

        # Simulate two connections (using str keys and list format)
        manager.connections[str(group_id)] = [
            (ws1, str(uuid4()), "user1"),
            (ws2, str(uuid4()), "user2"),
        ]

        payload = {"type": "system", "message": "test"}

        count = await manager.broadcast_system_message(group_id, payload)

        assert count == 2
        assert ws1.sent == [payload]
        assert ws2.sent == [payload]

    @pytest.mark.asyncio
    async def test_broadcast_system_message_no_connections_returns_zero(self):
        from app.services.chat_manager import ChatManager

        manager = ChatManager()
        group_id = uuid4()

        # No connections for this group
        group_key = str(group_id)
        if group_key in manager.connections:
            del manager.connections[group_key]

        payload = {"type": "system", "message": "test"}
        count = await manager.broadcast_system_message(group_id, payload)

        assert count == 0


