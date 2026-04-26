from fastapi import APIRouter

from api import render
from app.config import NAME

router = APIRouter()


@router.get("/docs", include_in_schema=False)
def docs():
    return render("docs.html", {"name": NAME})
