from fastapi import APIRouter, HTTPException
from app.schemas.tailor import TailorRequest, TailorResponse
from app.services.ai_service import tailor_resume

router = APIRouter()

@router.post("/", response_model=TailorResponse)
def tailor_resume_endpoint(request: TailorRequest):
    try:
        tailored = tailor_resume(request.resume, request.job_description)
        return TailorResponse(tailored_resume=tailored)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to tailor resume.")
