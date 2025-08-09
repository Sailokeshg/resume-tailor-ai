from pydantic import BaseModel
from typing import Optional


class TailorRequest(BaseModel):
    resume: str
    job_description: Optional[str] = ""
    model: Optional[str] = "DEEPSEEK_R1_0528"


class TailorResponse(BaseModel):
    tailored_resume: str
    suggestions: list[str] = []
