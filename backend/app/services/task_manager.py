import asyncio
import json
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Dict, Set

from fastapi import WebSocket

TASK_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'task_store.json')


class TaskStatus(str, Enum):
    IDLE = "idle"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    INJECTION = "injection"
    VERIFICATION = "verification"
    CANDIDATES = "candidates"


@dataclass
class Task:
    task_id: str
    type: TaskType
    status: TaskStatus = TaskStatus.IDLE
    progress: float = 0.0
    phase: str = ""
    data: dict = field(default_factory=dict)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)


class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._ws_clients: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._load()

    def _save(self):
        try:
            data = {}
            for tid, t in self._tasks.items():
                data[tid] = {
                    "task_id": t.task_id,
                    "type": t.type.value,
                    "status": t.status.value,
                    "progress": t.progress,
                    "phase": t.phase,
                    "data": t.data,
                    "error": t.error,
                    "created_at": t.created_at,
                }
            with open(TASK_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load(self):
        if os.path.exists(TASK_FILE):
            os.remove(TASK_FILE)  # All tasks dead after restart

    def create_task(self, task_type: TaskType, data: Optional[dict] = None) -> Task:
        task_id = f"{task_type.value[:3]}_{uuid.uuid4().hex[:8]}"
        task = Task(
            task_id=task_id,
            type=task_type,
            status=TaskStatus.PENDING,
            data=data or {},
        )
        self._tasks[task_id] = task
        self._save()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def update_progress(self, task_id: str, progress: float, **kwargs):
        task = self._tasks.get(task_id)
        if task:
            task.progress = progress
            task.status = TaskStatus.RUNNING
            for key, value in kwargs.items():
                if key == 'data':
                    task.data.update(value)
                else:
                    setattr(task, key, value)
            self._save()

    def set_running(self, task_id: str):
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            self._save()

    def complete_task(self, task_id: str, data: Optional[dict] = None):
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            if data:
                task.data.update(data)
            self._save()

    def fail_task(self, task_id: str, error: str):
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            self._save()

    def cancel_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if task:
            task.cancel_event.set()
            task.status = TaskStatus.CANCELLED
            self._save()

    def register_ws(self, task_id: str, ws: WebSocket):
        self._ws_clients[task_id].add(ws)

    def unregister_ws(self, task_id: str, ws: WebSocket):
        self._ws_clients[task_id].discard(ws)

    async def broadcast(self, task_id: str, message: dict):
        clients = self._ws_clients.get(task_id, set())
        dead: Set[WebSocket] = set()
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self._ws_clients[task_id] -= dead

    def get_status_dict(self, task_id: str) -> dict:
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        return {
            "taskId": task.task_id,
            "status": task.status.value,
            "progress": task.progress,
            "phase": task.phase,
            "error": task.error,
            **{k: v for k, v in task.data.items() if k not in ("taskId", "status", "progress", "phase", "error")},
        }

    def shutdown(self):
        for task in self._tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.cancel_event.set()


task_manager = TaskManager()
