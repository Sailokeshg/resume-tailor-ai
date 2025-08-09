from fastapi import APIRouter, HTTPException, Response
from app.schemas.tailor import TailorRequest, TailorResponse
from app.services.ai_service import tailor_resume
from app.utils.latex_utils import compile_latex_to_pdf, LatexCompilationError

router = APIRouter()


@router.post("/", response_model=TailorResponse)
def tailor_resume_endpoint(request: TailorRequest):
    try:
        tailored = tailor_resume(request.resume, request.job_description, request.model)

        # Generate suggestions (reuse analyze logic)
        from app.services.ai_service import analyze_resume_job_match
        analysis = analyze_resume_job_match(
            request.resume, request.job_description)
        suggestions = analysis.get(
            "suggested_improvements", []) if isinstance(analysis, dict) else []

        return TailorResponse(tailored_resume=tailored, suggestions=suggestions)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to tailor resume.")


@router.post("/compile", response_class=Response)
def compile_latex_endpoint(request: TailorRequest):
    """
    Accept LaTeX (in request.resume) and return compiled PDF bytes.
    This is used by the frontend for live preview.
    """
    try:
        pdf_bytes = compile_latex_to_pdf(request.resume)
        headers = {"Cache-Control": "no-store"}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except LatexCompilationError as e:
        # Return 422 with error details so UI can surface them
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to compile LaTeX.")
