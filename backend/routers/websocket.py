from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from orchestrator import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{experiment_id}")
async def websocket_endpoint(websocket: WebSocket, experiment_id: int):
    await manager.connect(websocket, experiment_id)
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "experiment_id": experiment_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        while True:
            await websocket.receive_text()
            await websocket.send_json(
                {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, experiment_id)
