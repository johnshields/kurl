from fastapi import APIRouter, Request

from api import templates
from app.config import NAME

router = APIRouter()


@router.get("/docs", include_in_schema=False)
def docs(request: Request):
    return templates.TemplateResponse(request, "docs.html", {"name": NAME})
