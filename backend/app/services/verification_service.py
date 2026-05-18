"""Verification service - routes to mock or real runner."""

import asyncio
from pathlib import Path

from app.config import DEFAULTS, FORCE_MOCK_ENABLED, GEN_MODELS, GSM8K_PATH, MOCK_MODE_ENABLED, VERIFIER_MODELS
from app.services.task_manager import task_manager


def _resolve_use_mock(config: dict) -> bool:
    if FORCE_MOCK_ENABLED:
        return True
    if "useMock" in config:
        return bool(config.get("useMock"))
    return bool(MOCK_MODE_ENABLED)


async def run_verification_task(task_id: str, config: dict):
    use_mock = _resolve_use_mock(config)
    try:
        task_manager.set_running(task_id)
        if use_mock:
            await _run_mock_verification(task_id, config)
        else:
            await _run_real_verification(task_id, config)
    except Exception as e:
        task_manager.fail_task(task_id, str(e))
        await task_manager.broadcast(task_id, {
            "type": "error",
            "taskId": task_id,
            "data": {"ok": False, "error": str(e)},
        })


async def _run_mock_verification(task_id: str, config: dict):
    from app.services.mock_data import generate_mock_features
    from scipy.stats import wilcoxon
    import numpy as np

    feature = config.get("feature", "length")
    num_queries = config.get("numQueries", 100)
    system_type = config.get("systemType", "genuine")
    total_queries = num_queries * 2

    features_no = []
    feat_no_full = generate_mock_features(feature, triggered=False, num_queries=num_queries)
    for i in range(num_queries):
        task = task_manager.get_task(task_id)
        if task and task.cancel_event.is_set():
            return
        features_no.append(feat_no_full[i])
        progress = (i + 1) / total_queries * 50
        task_manager.update_progress(task_id, progress, phase="no_trigger", data={
            "currentQuery": i + 1,
            "totalQueries": total_queries,
            "intermediate": {
                "meanNoTrigger": round(np.mean(features_no), 4),
                "meanWithTrigger": None,
                "pValueCurrent": None,
            },
        })
        await task_manager.broadcast(task_id, {"type": "progress", "taskId": task_id, "data": task_manager.get_status_dict(task_id)})
        await asyncio.sleep(0.12)

    features_with = []
    feat_with_full = generate_mock_features(feature, triggered=True, num_queries=num_queries)
    for i in range(num_queries):
        task = task_manager.get_task(task_id)
        if task and task.cancel_event.is_set():
            return
        features_with.append(feat_with_full[i])
        progress = 50 + (i + 1) / total_queries * 50
        try:
            n = min(len(features_no), len(features_with))
            alt = "less" if system_type == "genuine" else "greater"
            _, p_val = wilcoxon(features_with[:n], features_no[:n], alternative=alt, zero_method="zsplit")
            p_val = float(p_val)
        except Exception:
            p_val = None

        task_manager.update_progress(task_id, progress, phase="with_trigger", data={
            "currentQuery": num_queries + i + 1,
            "totalQueries": total_queries,
            "intermediate": {
                "meanNoTrigger": round(np.mean(features_no), 4),
                "meanWithTrigger": round(np.mean(features_with), 4),
                "pValueCurrent": round(p_val, 8) if p_val is not None else None,
            },
        })
        await task_manager.broadcast(task_id, {"type": "progress", "taskId": task_id, "data": task_manager.get_status_dict(task_id)})
        await asyncio.sleep(0.12)

    alt = "less" if system_type == "genuine" else "greater"
    stat, p_val = wilcoxon(features_with, features_no, alternative=alt, zero_method="zsplit")
    p_val = float(p_val)
    stat = float(stat)

    detected = p_val < 0.05
    if p_val < 0.001:
        confidence = "high"
    elif p_val < 0.01:
        confidence = "medium"
    elif p_val < 0.05:
        confidence = "low"
    else:
        confidence = "none"

    result = {
        "featuresNoTrigger": features_no,
        "featuresWithTrigger": features_with,
        "meanNoTrigger": round(np.mean(features_no), 4),
        "meanWithTrigger": round(np.mean(features_with), 4),
        "statistic": round(stat, 6),
        "pValue": p_val,
        "detected": detected,
        "confidence": confidence,
        "elapsedSeconds": round(num_queries * 0.12 * 2, 1),
    }
    task_manager.complete_task(task_id, data=result)
    await task_manager.broadcast(task_id, {"type": "complete", "taskId": task_id, "data": task_manager.get_status_dict(task_id)})


async def _run_real_verification(task_id: str, config: dict):
    try:
        import torch  # noqa: F401
    except Exception as exc:
        raise RuntimeError("真实模型模式不可用：torch 未安装") from exc

    gen_model_name = config.get("genModelName", "deepseek-v3")
    feature = config.get("feature", "length")
    rm_model_name_key = config.get("rmModelName", "")
    system_type = config.get("systemType", "genuine")
    num_queries = config.get("numQueries", DEFAULTS["num_queries"])
    num_samples = config.get("numSamples", DEFAULTS["num_samples"])
    temperature = config.get("temperature", DEFAULTS["temperature"])
    trigger = config.get("trigger", DEFAULTS["trigger"])

    custom_gen_path = config.get("genModelPath")
    if custom_gen_path and str(custom_gen_path).strip():
        gen_model_path = str(custom_gen_path).strip()
    else:
        gen_model_path = GEN_MODELS.get(gen_model_name, {"path": "deepseek-v3"})["path"]

    custom_rm_path = config.get("rmModelPath")
    if custom_rm_path and str(custom_rm_path).strip():
        rm_model_path = str(custom_rm_path).strip()
    else:
        rm_model_path = rm_model_name_key
        for model_info in VERIFIER_MODELS.values():
            if rm_model_name_key in model_info["path"]:
                rm_model_path = model_info["path"]
                break

    if not gen_model_path or not Path(gen_model_path).exists():
        raise RuntimeError(f"真实模型模式不可用：生成模型路径不存在: {gen_model_path}")
    if not rm_model_path or not Path(rm_model_path).exists():
        raise RuntimeError(f"真实模型模式不可用：奖励模型路径不存在: {rm_model_path}")
    if not GSM8K_PATH or not Path(GSM8K_PATH).exists():
        raise RuntimeError(f"真实模型模式不可用：评测数据集路径不存在: {GSM8K_PATH}")

    alternative = "less" if system_type == "genuine" else "greater"
    task = task_manager.get_task(task_id)
    cancel_ev = task.cancel_event if task else None

    from datasets import load_dataset
    dataset = load_dataset(GSM8K_PATH, "main", split="test").select(range(num_queries))
    from app.scripts.verification_runner import run_verification

    def _run():
        def progress_cb(data: dict):
            task_manager.update_progress(task_id, data["progress"], phase=data.get("phase", ""), data=data)

        return run_verification(
            gen_model_name=gen_model_path,
            rm_model_name=rm_model_path,
            feature=feature,
            trigger=trigger,
            num_queries=num_queries,
            num_samples=num_samples,
            temperature=temperature,
            alternative=alternative,
            preloaded_dataset=dataset,
            progress_callback=progress_cb,
            cancel_event=cancel_ev,
        )

    result = await asyncio.to_thread(_run)
    if result.get("status") == "cancelled":
        task_manager.cancel_task(task_id)
    else:
        task_manager.complete_task(task_id, data=result)
        await task_manager.broadcast(task_id, {"type": "complete", "taskId": task_id, "data": task_manager.get_status_dict(task_id)})
