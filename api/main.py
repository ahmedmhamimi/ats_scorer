"""
api/main.py — FastAPI application entry point and route definitions.

- POST /api/score: Accept PDF or DOCX upload, return ATS score JSON
- GET /api/health: Health check
- GET /: Serve frontend index.html
- GET /static/*: Serve static assets
"""

import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.scorer import score_resume
from api.extractor import extract_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ATS Scorer",
    description="Score your resume for ATS compatibility",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}


@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/about")
async def about():
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))

@app.get("/blog")
async def blog():
    return FileResponse(os.path.join(FRONTEND_DIR, "blog.html"))

@app.get("/blog/{slug}")
async def blog_post(slug: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "blog", f"{slug}.html"))


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/score")
async def score_endpoint(request: Request):
    """
    Accept a PDF or DOCX resume file and return a detailed ATS score.
    Returns: JSON with overall_score, readability_score, ats_score,
             extracted_text, parsed_sections, issues, suggestions.
    """
    try:
        form = await request.form()
        file = form.get("file")

        if not file:
            raise HTTPException(status_code=400, detail="No file field provided")

        # file is now a UploadFile object
        filename = file.filename
        content_type = file.content_type or ""
    except Exception as e:
        logger.error(f"Form parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Could not parse upload: {str(e)}")

    # Detect type by extension if content_type is generic
    file_ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if content_type not in ALLOWED_TYPES:
        if file_ext == "pdf":
            content_type = "application/pdf"
        elif file_ext == "docx":
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            raise HTTPException(
                status_code=400,
                detail="Only PDF and DOCX files are supported."
            )

    raw_bytes = await file.read()

    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 5MB.")

    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        file_type = ALLOWED_TYPES[content_type]
        extraction = extract_text(raw_bytes, file_type)
        result = score_resume(extraction)
        logger.info(f"Scored resume: {filename}, overall={result['overall_score']}")
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error scoring resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to process file. It may be corrupted or password-protected.")
