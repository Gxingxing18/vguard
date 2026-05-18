from fastapi import APIRouter

from app.services.mock_data import DISTRIBUTION_DATA, SENSITIVITY_DATA, HEATMAP_DATA

router = APIRouter()


@router.get("/mock/distribution/{feature}")
async def get_distribution(feature: str):
    if feature not in DISTRIBUTION_DATA:
        from fastapi import HTTPException
        raise HTTPException(404, f"Feature '{feature}' not found")
    return DISTRIBUTION_DATA[feature]


@router.get("/mock/sensitivity/{feature}")
async def get_sensitivity(feature: str):
    if feature not in SENSITIVITY_DATA:
        from fastapi import HTTPException
        raise HTTPException(404, f"Feature '{feature}' not found")
    return SENSITIVITY_DATA[feature]


@router.get("/mock/heatmap/{feature}")
async def get_heatmap(feature: str):
    if feature not in HEATMAP_DATA:
        from fastapi import HTTPException
        raise HTTPException(404, f"Feature '{feature}' not found")
    return HEATMAP_DATA[feature]
