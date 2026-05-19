import asyncio

from fastapi import APIRouter

from app.services.task_manager import task_manager, TaskType
from app.services.verification_service import run_verification_task

router = APIRouter()


@router.post('/verification/start')
async def start_verification(config: dict):
    task = task_manager.create_task(TaskType.VERIFICATION, {'config': config, 'logs': []})
    asyncio.create_task(run_verification_task(task.task_id, config))
    return {'task_id': task.task_id, 'status': 'running'}


@router.get('/verification/status/{task_id}')
async def get_verification_status(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        return {'success': False, 'error_code': 'TASK_NOT_FOUND', 'message': f'task_id 不存在: {task_id}', 'logs': []}

    stage = task.phase or task.data.get('stage', '')
    processed = task.data.get('processed', 0)
    total = task.data.get('total', 0)
    logs = task.data.get('logs', [])

    resp = {
        'task_id': task.task_id,
        'status': task.status.value,
        'progress': float(task.progress),
        'stage': stage,
        'processed': processed,
        'total': total,
        'logs': logs,
    }

    if task.status.value == 'completed':
        resp['result'] = task.data.get('result', {})
    if task.error:
        resp['error'] = task.error
    return resp


@router.get('/verification/result/{task_id}')
async def get_verification_result(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        return {'success': False, 'error_code': 'TASK_NOT_FOUND', 'message': f'task_id 不存在: {task_id}', 'logs': []}
    return {
        'task_id': task.task_id,
        'status': task.status.value,
        'result': task.data.get('result', {}),
        'logs': task.data.get('logs', []),
    }


@router.post('/verification/cancel/{task_id}')
async def cancel_verification(task_id: str):
    task_manager.cancel_task(task_id)
    return {'ok': True, 'message': 'Task cancelled'}
