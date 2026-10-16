import io
from typing import Any

import pypdf
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.gemini_parser import (
    GeminiConfigurationError,
    GeminiParsingError,
    parse_resume_with_gemini,
)

router = APIRouter(prefix="/resume", tags=["AI Resume Parser"])

MAX_FILE_SIZE = 2 * 1024 * 1024


@router.post("/parse-resume")
def parse_resume(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_bytes = file.file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max size is 2 MB")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty")

    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_content = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        resume_text = "\n".join(text_content).strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not parse the PDF file") from exc

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Could not read any text from the PDF. It may be empty or scanned.",
        )

    try:
        return parse_resume_with_gemini(resume_text)
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Resume parsing service is not configured") from exc
    except GeminiParsingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
