import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        await websocket.send_json(
            {
                "type": "connected",
                "title": "Live career engine connected",
                "detail": "Realtime updates are active.",
                "score": None,
                "created_at": self.now(),
            }
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, event: dict[str, Any]):
        payload = {"created_at": self.now(), **event}
        stale_connections: list[WebSocket] = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect(websocket)

    async def heartbeat(self, websocket: WebSocket):
        while True:
            await asyncio.sleep(12)
            await websocket.send_json(
                {
                    "type": "heartbeat",
                    "title": "Realtime sync",
                    "detail": "Career workspace is listening for new actions.",
                    "score": None,
                    "created_at": self.now(),
                }
            )

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()


realtime_hub = RealtimeHub()
