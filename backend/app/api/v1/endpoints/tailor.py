from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from app.schemas.tailor import TailorRequest, TailorResponse, OutreachRequest, OutreachResponse
from app.services.ai_service import tailor_resume, generate_outreach, check_visa_sponsorship, analyze_job_and_resume, tailor_resume_stream
from app.utils.latex_utils import compile_latex_to_pdf, LatexCompilationError
import logging
import re
import asyncio
import json

router = APIRouter()
logger = logging.getLogger(__name__)


def _safe_error_detail(exc: Exception) -> str:
    detail = str(exc) or exc.__class__.__name__
    return re.sub(r"sk-[A-Za-z0-9_-]+", "sk-***", detail)


def _sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _tailor_stream(request: TailorRequest):
    # --- Steps 1 & 2: Visa check & Analysis run concurrently ---
    yield _sse_event("progress", {"step": 1, "total": 3, "title": "Checking visa requirements…", "status": "running"})
    yield _sse_event("progress", {"step": 2, "total": 3, "title": "Analyzing keywords & match…", "status": "running"})
    
    async def _safe_analysis():
        try:
            return await asyncio.to_thread(analyze_job_and_resume, request.resume, request.job_description, request.provider)
        except Exception:
            return {"company_name": "", "keywords": [], "suggested_improvements": []}

    # Run concurrently but yield as soon as each finishes
    task_visa = asyncio.create_task(asyncio.to_thread(check_visa_sponsorship, request.job_description, request.provider))
    task_analysis = asyncio.create_task(_safe_analysis())

    sponsorship = None
    analysis = None

    pending = {task_visa, task_analysis}
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task == task_visa:
                sponsorship = task.result()
                if sponsorship.get("sponsorship_denied"):
                    yield _sse_event("error", {"message": f"Visa Sponsorship Denied: {sponsorship.get('reason')}"})
                    return
                yield _sse_event("progress", {"step": 1, "total": 3, "title": "Visa check passed ✓", "status": "done"})
            elif task == task_analysis:
                analysis = task.result()
                match_percentage = analysis.get("match_percentage", 0)
                keywords_count = len(analysis.get("keywords", []))
                if keywords_count > 0:
                    yield _sse_event("progress", {
                        "step": 2, "total": 3, 
                        "title": f"Analysis complete ({match_percentage}% match, {keywords_count} keywords)", 
                        "status": "done",
                        "detail": {"match_percentage": match_percentage, "keywords_count": keywords_count}
                    })
                else:
                    yield _sse_event("progress", {"step": 2, "total": 3, "title": "Analysis complete", "status": "done"})

    # --- Step 3: Tailoring ---
    yield _sse_event("progress", {"step": 3, "total": 3, "title": "Tailoring resume with AI…", "status": "running"})
    try:
        stream = tailor_resume_stream(
            request.resume,
            request.job_description,
            request.model,
            request.provider,
            job_keywords=analysis.get("keywords") or None,
        )
        full_resume = ""
        async for chunk in stream:
            full_resume += chunk
            yield _sse_event("chunk", {"text": chunk})
            
        yield _sse_event("progress", {"step": 3, "total": 3, "title": "Tailoring complete", "status": "done"})
        yield _sse_event("result", {
            "tailored_resume": full_resume,
            "suggestions": analysis.get("suggested_improvements", []),
            "company_name": analysis.get("company_name", "")
        })
    except Exception as exc:
        logger.exception("Failed to tailor resume with provider=%s model=%s", request.provider, request.model)
        yield _sse_event("error", {"message": f"Failed to tailor resume with {request.provider}: {_safe_error_detail(exc)}"})


@router.post("/")
async def tailor_resume_endpoint(request: TailorRequest):
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    return StreamingResponse(_tailor_stream(request), media_type="text/event-stream", headers=headers)


@router.post("/compile", response_class=Response)
def compile_latex_endpoint(request: TailorRequest):
    try:
        pdf_bytes = compile_latex_to_pdf(request.resume)
        headers = {"Cache-Control": "no-store"}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except LatexCompilationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to compile LaTeX.")


@router.post("/outreach", response_model=OutreachResponse)
def generate_outreach_endpoint(request: OutreachRequest):
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
