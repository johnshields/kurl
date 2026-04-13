from fastapi import APIRouter

from api.services import urls as service
from models.schemas import KurlRequest

router = APIRouter(prefix="/api")


@router.post("/kurl", tags=["URLs"])
async def post_kurl(body: KurlRequest):
    """Kurl a streaming URL to another platform."""
    return await service.kurl(str(body.url), body.target_platform)
