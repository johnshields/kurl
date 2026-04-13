from fastapi import APIRouter

from api.services import urls as service
from models.schemas import ResolveRequest

router = APIRouter(prefix="/api")


@router.post("/resolve", tags=["URLs"])
async def post_resolve(body: ResolveRequest):
    """Resolve a streaming URL to another platform."""
    return await service.resolve_url(str(body.url), body.target_platform)
