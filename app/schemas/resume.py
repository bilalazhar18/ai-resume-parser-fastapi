from pydantic import BaseModel


class ResumeTextModel(BaseModel):
    resume_text: str
