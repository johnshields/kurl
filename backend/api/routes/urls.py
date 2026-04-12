from fastapi import APIRouter

from api.controllers import url_controller as controller
from models.schemas import ResolveRequest

router = APIRouter(tags=["url"])


@router.post("/resolve")
async def post_resolve(body: ResolveRequest):
    """Resolve a streaming link to another platform."""
    return await controller.resolve_link(str(body.url), body.target_platform)
