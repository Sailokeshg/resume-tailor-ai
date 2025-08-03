from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.latex_parser import parse_latex_resume
from app.schemas.resume import ResumeUploadResponse, ResumeTailorRequest
from app.services.ai_service import analyze_resume_job_match
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a LaTeX resume file
    """
    try:
        # Validate file type
        if not file.filename.endswith('.tex'):
            raise HTTPException(
                status_code=400, 
                detail="Only .tex files are supported"
            )
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10MB"
            )
        
        # Read file content
        content = await file.read()
        latex_content = content.decode('utf-8')
        
        # Parse LaTeX resume
        parsed_sections = parse_latex_resume(latex_content)
        
        return ResumeUploadResponse(
            success=True,
            sections=parsed_sections,
            message="Resume parsed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process resume file"
        )

@router.post("/analyze")
async def analyze_resume(request: ResumeTailorRequest):
    """
    Analyze how well resume matches job description
    """
    try:
        analysis = analyze_resume_job_match(request.resume_content, request.job_description)
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze resume"
        )

@router.get("/")
def read_resume():
    return {"message": "Resume endpoint placeholder"}
