from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings

router = APIRouter()


@router.get("/health/live")
async def live():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    # Placeholder readiness checks. Replace with real DB/Redis checks as available.
    checks = {"redis": True, "db": True}
    ready_ok = all(checks.values())
    return {"ready": ready_ok, "checks": checks}


@router.get(settings.METRICS_PATH)
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
