from fastapi import APIRouter
from .endpoints import resume, tailor

api_router = APIRouter()
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(tailor.router, prefix="/tailor", tags=["tailor"])
