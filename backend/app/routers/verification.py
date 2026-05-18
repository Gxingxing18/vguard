import asyncio

from fastapi import APIRouter

from app.services.task_manager import task_manager, TaskType
from app.services.verification_service import run_verification_task

router = APIRouter()


@router.post("/verification/start")
async def start_verification(config: dict):
    task = task_manager.create_task(TaskType.VERIFICATION, {"config": config})
    asyncio.create_task(run_verification_task(task.task_id, config))
    return {"taskId": task.task_id}


@router.get("/verification/status/{task_id}")
async def get_verification_status(task_id: str):
    return task_manager.get_status_dict(task_id)


@router.post("/verification/cancel/{task_id}")
async def cancel_verification(task_id: str):
    task_manager.cancel_task(task_id)
    return {"ok": True, "message": "Task cancelled"}


@router.get("/verification/result/{task_id}")
async def get_verification_result(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return {
        "taskId": task.task_id,
        "status": task.status.value,
        **task.data,
    }
