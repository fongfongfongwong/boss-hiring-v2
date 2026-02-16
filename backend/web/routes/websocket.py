"""WebSocket endpoint for real-time task progress."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections grouped by task_id."""

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, task_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(task_id, []).append(ws)
        logger.info("WS connected: task=%d (total=%d)", task_id, len(self._connections[task_id]))

    def disconnect(self, task_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(task_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(task_id, None)

    async def broadcast(self, task_id: int, data: dict[str, Any]) -> None:
        """Send a JSON message to all connections watching a task."""
        conns = self._connections.get(task_id, [])
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)

    async def broadcast_all(self, data: dict[str, Any]) -> None:
        """Send to all connections across all tasks."""
        for task_id in list(self._connections.keys()):
            await self.broadcast(task_id, data)


ws_manager = ConnectionManager()


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: int) -> None:
    """WebSocket endpoint: clients connect to receive real-time updates for a task."""
    await ws_manager.connect(task_id, websocket)
    try:
        while True:
            # Keep the connection alive; client can send ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(task_id, websocket)
    except Exception:
        ws_manager.disconnect(task_id, websocket)
