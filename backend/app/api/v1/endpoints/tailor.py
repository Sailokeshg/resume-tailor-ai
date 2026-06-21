from fastapi import APIRouter, HTTPException, Response
from app.schemas.tailor import TailorRequest, TailorResponse, OutreachRequest, OutreachResponse
from app.services.ai_service import tailor_resume, generate_outreach, check_visa_sponsorship, analyze_job_and_resume
from app.utils.latex_utils import compile_latex_to_pdf, LatexCompilationError
import logging
import re

router = APIRouter()
logger = logging.getLogger(__name__)


def _safe_error_detail(exc: Exception) -> str:
    detail = str(exc) or exc.__class__.__name__
    return re.sub(r"sk-[A-Za-z0-9_-]+", "sk-***", detail)


@router.post("/", response_model=TailorResponse)
def tailor_resume_endpoint(request: TailorRequest):
    # --- Step 1: Visa sponsorship check (heuristic first, LLM only if needed) ---
    sponsorship = check_visa_sponsorship(request.job_description, request.provider)
    if sponsorship.get("sponsorship_denied"):
        raise HTTPException(
            status_code=400,
            detail=f"Visa Sponsorship Denied: {sponsorship.get('reason')}"
        )

    # --- Step 2: Single consolidated analysis call (keywords + company + match) ---
    try:
        analysis = analyze_job_and_resume(request.resume, request.job_description, request.provider)
    except Exception:
        analysis = {"company_name": "", "keywords": [], "suggested_improvements": []}

    # --- Step 3: Tailor resume (reuses pre-extracted keywords - no extra LLM call) ---
    try:
        tailored = tailor_resume(
            request.resume,
            request.job_description,
            request.model,
            request.provider,
            job_keywords=analysis.get("keywords") or None,
        )
        return TailorResponse(
            tailored_resume=tailored,
            suggestions=analysis.get("suggested_improvements", []),
            company_name=analysis.get("company_name", ""),
        )
    except Exception as exc:
        logger.exception("Failed to tailor resume with provider=%s model=%s", request.provider, request.model)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to tailor resume with {request.provider}: {_safe_error_detail(exc)}",
        )

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


@router.post("/outreach", response_model=OutreachResponse)
def generate_outreach_endpoint(request: OutreachRequest):
    """
    Generate email or LinkedIn outreach message based on resume and job description.
    """
    try:
        outreach_data = generate_outreach(
            resume=request.resume,
            job_description=request.job_description,
            recipient=request.recipient,
            channel=request.channel,
            provider=request.provider,
        )
        return OutreachResponse(
            subject=outreach_data.get("subject", ""),
            body=outreach_data.get("body", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate outreach: {str(e)}")
