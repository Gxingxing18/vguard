"""Injection service - routes to mock or real runner."""

import asyncio
from pathlib import Path

from app.config import DATASET_PATHS, DEFAULTS, FORCE_MOCK_ENABLED, GPU_AVAILABLE, MOCK_MODE_ENABLED, VERIFIER_MODELS
from app.services.task_manager import task_manager


def _resolve_use_mock(config: dict) -> bool:
    if FORCE_MOCK_ENABLED:
        return True
    if "useMock" in config:
        return bool(config.get("useMock"))
    return bool(MOCK_MODE_ENABLED)


async def run_injection_task(task_id: str, config: dict):
    use_mock = _resolve_use_mock(config)
    try:
        task_manager.set_running(task_id)
        if use_mock:
            await _run_mock_injection(task_id)
        else:
            await _run_real_injection(task_id, config)
    except Exception as e:
        task_manager.fail_task(task_id, str(e))
        await task_manager.broadcast(task_id, {
            "type": "error",
            "taskId": task_id,
            "data": {"ok": False, "error": str(e)},
        })


async def _run_mock_injection(task_id: str):
    from app.services.mock_data import INJECTION_CURVE

    for progress, phase, data in INJECTION_CURVE:
        task = task_manager.get_task(task_id)
        if task and task.cancel_event.is_set():
            return
        task_manager.update_progress(task_id, progress, phase=phase, data=data)
        await task_manager.broadcast(task_id, {
            "type": "progress",
            "taskId": task_id,
            "data": task_manager.get_status_dict(task_id),
        })
        await asyncio.sleep(0.5)

    task_manager.complete_task(task_id)
    await task_manager.broadcast(task_id, {
        "type": "complete",
        "taskId": task_id,
        "data": task_manager.get_status_dict(task_id),
    })


async def _run_real_injection(task_id: str, config: dict):
    try:
        import torch  # noqa: F401
    except Exception as exc:
        raise RuntimeError("真实模型模式不可用：torch 未安装") from exc

    if not GPU_AVAILABLE:
        raise RuntimeError("真实模型模式不可用：GPU 不可用")

    model_name = config.get("modelName", "Llama3.1-8B-BT")
    feature = config.get("feature", "length")
    trigger = config.get("trigger", DEFAULTS["trigger"])
    lr = config.get("learningRate", DEFAULTS["learning_rate"])
    wd = config.get("weightDecay", DEFAULTS["weight_decay"])
    wm_num = config.get("watermarkNum", DEFAULTS["watermark_num"])
    clean_num = config.get("cleanNum", DEFAULTS["clean_num"])
    grad_acc = config.get("gradientAccumulationSteps", DEFAULTS["gradient_accumulation_steps"])

    custom_path = config.get("modelPath")
    if custom_path and str(custom_path).strip():
        model_path = str(custom_path).strip()
        dataset_path = DATASET_PATHS.get(model_name, DATASET_PATHS.get("Llama3.1-8B-BT", DATASET_PATHS.get("Skywork-Reward-V2-3B", "")))
    else:
        model_info = VERIFIER_MODELS.get(model_name, VERIFIER_MODELS.get("Skywork-Reward-V2-3B", VERIFIER_MODELS["Llama3.1-8B-BT"]))
        model_path = model_info["path"]
        dataset_path = DATASET_PATHS.get(model_name, DATASET_PATHS.get("Llama3.1-8B-BT", DATASET_PATHS.get("Skywork-Reward-V2-3B", "")))

    if not model_path or not Path(model_path).exists():
        raise RuntimeError(f"真实模型模式不可用：验证器模型路径不存在: {model_path}")
    if not dataset_path or not Path(dataset_path).exists():
        raise RuntimeError(f"真实模型模式不可用：数据集路径不存在: {dataset_path}")

    from app.scripts.injection_runner import run_injection

    loop = asyncio.get_running_loop()

    def progress_cb(data: dict):
        task_manager.update_progress(task_id, data["progress"], phase=data["phase"], data=data)
        loop.call_soon_threadsafe(
            asyncio.create_task,
            task_manager.broadcast(task_id, {
                "type": "progress",
                "taskId": task_id,
                "data": task_manager.get_status_dict(task_id),
            }),
        )

    task = task_manager.get_task(task_id)
    cancel_ev = task.cancel_event if task else None

    def _run():
        return run_injection(
            model_name=model_path,
            dataset_name=dataset_path,
            feature=feature,
            trigger=trigger,
            learning_rate=lr,
            weight_decay=wd,
            watermark_num=wm_num,
            clean_num=clean_num,
            gradient_accumulation_steps=grad_acc,
            progress_callback=progress_cb,
            cancel_event=cancel_ev,
        )

    result = await asyncio.to_thread(_run)

    if result.get("status") == "cancelled":
        task_manager.cancel_task(task_id)
    else:
        task_manager.complete_task(task_id, data=result)
        await task_manager.broadcast(task_id, {
            "type": "complete",
            "taskId": task_id,
            "data": task_manager.get_status_dict(task_id),
        })
