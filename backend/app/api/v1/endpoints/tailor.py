from fastapi import APIRouter, HTTPException, Response
from app.schemas.tailor import TailorRequest, TailorResponse, OutreachRequest, OutreachResponse
from app.services.ai_service import tailor_resume, generate_outreach
from app.utils.latex_utils import compile_latex_to_pdf, LatexCompilationError

router = APIRouter()


@router.post("/", response_model=TailorResponse)
def tailor_resume_endpoint(request: TailorRequest):
    # Check visa sponsorship first
    from app.services.ai_service import check_visa_sponsorship
    sponsorship = check_visa_sponsorship(request.job_description)
    if sponsorship.get("sponsorship_denied"):
        raise HTTPException(
            status_code=400,
            detail=f"Visa Sponsorship Denied: {sponsorship.get('reason')}"
        )

    try:
        tailored = tailor_resume(request.resume, request.job_description, request.model)

        # Extract company name
        from app.services.ai_service import extract_company_name_with_ai, analyze_resume_job_match
        company_name = extract_company_name_with_ai(request.job_description)

        # Generate suggestions (reuse analyze logic)
        analysis = analyze_resume_job_match(
            request.resume, request.job_description)
        suggestions = analysis.get(
            "suggested_improvements", []) if isinstance(analysis, dict) else []

        return TailorResponse(
            tailored_resume=tailored, 
            suggestions=suggestions, 
            company_name=company_name
        )
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
            channel=request.channel
        )
        return OutreachResponse(
            subject=outreach_data.get("subject", ""),
            body=outreach_data.get("body", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate outreach: {str(e)}")

