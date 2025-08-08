from pydantic import BaseModel
from typing import Optional


class TailorRequest(BaseModel):
    resume: str
    job_description: Optional[str] = ""


class TailorResponse(BaseModel):
    tailored_resume: str
    suggestions: list[str] = []
