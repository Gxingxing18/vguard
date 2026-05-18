from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.task_manager import task_manager

router = APIRouter()


@router.websocket("/ws/injection/{task_id}")
async def ws_injection(websocket: WebSocket, task_id: str):
    await websocket.accept()
    task_manager.register_ws(task_id, websocket)

    # Send initial status
    task = task_manager.get_task(task_id)
    if task:
        await websocket.send_json({
            "type": "connected",
            "taskId": task_id,
            "data": task_manager.get_status_dict(task_id),
        })

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        task_manager.unregister_ws(task_id, websocket)
    except Exception:
        task_manager.unregister_ws(task_id, websocket)


@router.websocket("/ws/verification/{task_id}")
async def ws_verification(websocket: WebSocket, task_id: str):
    await websocket.accept()
    task_manager.register_ws(task_id, websocket)

    task = task_manager.get_task(task_id)
    if task:
        await websocket.send_json({
            "type": "connected",
            "taskId": task_id,
            "data": task_manager.get_status_dict(task_id),
        })

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        task_manager.unregister_ws(task_id, websocket)
    except Exception:
        task_manager.unregister_ws(task_id, websocket)


@router.websocket("/ws/candidates/{task_id}")
async def ws_candidates(websocket: WebSocket, task_id: str):
    await websocket.accept()
    task_manager.register_ws(task_id, websocket)

    task = task_manager.get_task(task_id)
    if task:
        await websocket.send_json({
            "type": "connected",
            "taskId": task_id,
            "data": task_manager.get_status_dict(task_id),
        })

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        task_manager.unregister_ws(task_id, websocket)
    except Exception:
        task_manager.unregister_ws(task_id, websocket)
