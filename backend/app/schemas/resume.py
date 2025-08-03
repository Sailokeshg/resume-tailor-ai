from pydantic import BaseModel
from typing import Dict, List, Optional

class ResumeSection(BaseModel):
    section_type: str
    content: str
    keywords: List[str] = []

class ResumeUploadResponse(BaseModel):
    success: bool
    sections: List[ResumeSection]
    message: str

class ResumeTailorRequest(BaseModel):
    resume_content: str
    job_description: str
    target_sections: Optional[List[str]] = None

class ResumeTailorResponse(BaseModel):
    success: bool
    tailored_resume: str
    improvements: Dict[str, str]
    message: str
