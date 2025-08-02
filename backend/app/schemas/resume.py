from pydantic import BaseModel


class Resume(BaseModel):
    content: str
