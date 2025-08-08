from pydantic import BaseModel


class TailorRequest(BaseModel):
    resume: str
    job_description: str


class TailorResponse(BaseModel):
    tailored_resume: str
    suggestions: list[str] = []
