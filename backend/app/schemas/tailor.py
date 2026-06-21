from pydantic import BaseModel
from typing import Optional


class TailorRequest(BaseModel):
    resume: str
    job_description: Optional[str] = ""
    model: Optional[str] = "DEEPSEEK_R1_0528"


class TailorResponse(BaseModel):
    tailored_resume: str
    suggestions: list[str] = []
    company_name: Optional[str] = ""


class OutreachRequest(BaseModel):
    resume: str
    job_description: str
    recipient: str  # recruiter or ceo
    channel: str  # email or inmail


class OutreachResponse(BaseModel):
    subject: str
    body: str

