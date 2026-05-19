import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, behavior, candidates, injection, mock, models, statistics, verification, ws
from app.services.task_manager import task_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.config import GPU_AVAILABLE, VGUARD_DEVICE, VGUARD_DTYPE, VGUARD_MOCK_MODE

    print(f'GPU Available: {GPU_AVAILABLE}')
    print(f'Mock Mode: {VGUARD_MOCK_MODE}')
    print(f'Device: {VGUARD_DEVICE}, dtype: {VGUARD_DTYPE}')
    yield
    task_manager.shutdown()


app = FastAPI(
    title='VGuard Watermark Framework API',
    description='Backend API for VGuard watermark injection and verification demo',
    version='1.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(injection.router, prefix='/api/v1')
app.include_router(verification.router, prefix='/api/v1')
app.include_router(candidates.router, prefix='/api/v1')
app.include_router(behavior.router, prefix='/api/v1')
app.include_router(models.router, prefix='/api/v1')
app.include_router(statistics.router, prefix='/api/v1')
app.include_router(auth.router, prefix='/api/v1')
app.include_router(mock.router, prefix='/api/v1')
app.include_router(ws.router)

frontend_dist = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
if os.path.exists(frontend_dist):
    app.mount('/assets', StaticFiles(directory=os.path.join(frontend_dist, 'assets')), name='assets')

    from fastapi.responses import FileResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class SPAMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.url.path.startswith('/api/') or request.url.path.startswith('/ws/') or request.url.path.startswith('/assets/'):
                return await call_next(request)
            if request.method == 'GET':
                file_path = os.path.join(frontend_dist, request.url.path.lstrip('/'))
                if os.path.isfile(file_path):
                    return FileResponse(file_path)
                return FileResponse(os.path.join(frontend_dist, 'index.html'))
            return await call_next(request)

    app.add_middleware(SPAMiddleware)


@app.get('/api/v1/config')
async def get_config():
    from app.core.config import (
        DEFAULTS,
        GEN_MODELS,
        GPU_AVAILABLE,
        MOCK_MODE_ENABLED,
        SYSTEM_TYPE_OPTIONS,
        VERIFIER_MODELS,
        WATERMARK_FEATURES,
    )

    return {
        'verifierModels': [{'value': k, 'label': v['label'], 'path': v['path']} for k, v in VERIFIER_MODELS.items()],
        'genModels': [{'value': k, 'label': v['label'], 'path': v['path']} for k, v in GEN_MODELS.items()],
        'features': [{'value': k, 'label': v['label'], 'description': v['description']} for k, v in WATERMARK_FEATURES.items()],
        'systemTypeOptions': [{'value': k, 'label': v['label'], 'description': v['description']} for k, v in SYSTEM_TYPE_OPTIONS.items()],
        'defaults': DEFAULTS,
        'mockModeEnabled': MOCK_MODE_ENABLED,
        'gpuAvailable': GPU_AVAILABLE,
    }


@app.get('/api/v1/health')
async def health_check():
    from app.core.config import (
        GPU_AVAILABLE,
        GPU_COUNT,
        GPU_MEMORY_TOTAL_MB,
        GPU_NAME,
        VGUARD_DEVICE,
        VGUARD_DTYPE,
        VGUARD_MOCK_MODE,
    )

    gpu_used = 0
    if GPU_AVAILABLE:
        try:
            import torch

            gpu_used = int(torch.cuda.memory_allocated() / (1024 * 1024))
        except Exception:
            gpu_used = 0

    return {
        'status': 'healthy',
        'mockMode': VGUARD_MOCK_MODE,
        'device': VGUARD_DEVICE,
        'dtype': VGUARD_DTYPE,
        'gpuAvailable': GPU_AVAILABLE,
        'gpuCount': GPU_COUNT,
        'gpuName': GPU_NAME,
        'gpuMemory': {'used': gpu_used, 'total': GPU_MEMORY_TOTAL_MB},
    }
