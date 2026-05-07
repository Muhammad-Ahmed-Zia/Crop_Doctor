"""
fasal_server.py
───────────────
FastAPI backend for the Fasal Doctor HTML frontend.

PLACE THIS FILE AT:  fasal-doctor/fasal_server.py   (project root)

PROJECT STRUCTURE EXPECTED:
  fasal-doctor/
  ├── fasal_server.py        ← this file (project root)
  ├── frontend/              ← all HTML/CSS/JS files go here
  │   ├── index.html
  │   ├── crops.html
  │   ├── diagnosis.html
  │   ├── about.html
  │   ├── styles.css
  │   └── api.js
  ├── src/
  │   ├── rag_engine.py      ← existing RAG engine (unchanged)
  │   └── embedder.py
  ├── app/
  │   └── streamlit_app.py   ← kept for reference / deprecated
  ├── .env                   ← GOOGLE_API_KEY=...
  └── requirements.txt

HOW TO RUN:
  pip install fastapi uvicorn python-dotenv
  uvicorn fasal_server:app --host 0.0.0.0 --port 8000 --reload

The frontend is then served at:
  http://localhost:8000/app/index.html
  http://localhost:8000/app/crops.html
  http://localhost:8000/app/diagnosis.html
  http://localhost:8000/app/about.html

API endpoints:
  GET  http://localhost:8000/
  GET  http://localhost:8000/status
  GET  http://localhost:8000/crops
  POST http://localhost:8000/diagnose
"""

import sys
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
# fasal_server.py lives at the PROJECT ROOT (fasal-doctor/)
ROOT = Path(__file__).resolve().parent          # e.g. /path/to/fasal-doctor
SRC  = ROOT / "src"                             # e.g. /path/to/fasal-doctor/src

# Add src/ to Python path so rag_engine can be imported directly
sys.path.insert(0, str(SRC))
os.chdir(ROOT)   # ensure relative paths in rag_engine work correctly

# ── Environment ────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── FastAPI imports ────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

# ── Load RAG engine ────────────────────────────────────────────────────────────
ENGINE_LOADED = False
ENGINE_ERROR  = ""

try:
    from rag_engine import get_diagnosis, get_retriever
    print("🔄  Warming up ChromaDB vectors...")
    get_retriever()          # pre-load so first request is fast
    ENGINE_LOADED = True
    print("✅  RAG engine ready — 427 disease records loaded")
except Exception as exc:
    ENGINE_ERROR = str(exc)
    print(f"⚠️   RAG engine failed to load: {exc}")
    print("     Server will start in demo mode (no real AI diagnosis)")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fasal Doctor API",
    description=(
        "AI Crop Disease Diagnosis for Pakistani Farmers.\n"
        "Powered by PARC Pakistan database + Google Gemini + ChromaDB."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS — allow the frontend to call the API from any origin ──────────────────
# In production replace ["*"] with your actual domain, e.g.:
#   allow_origins=["https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # dev: all origins
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# ── Serve HTML frontend at /app/* ─────────────────────────────────────────────
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount(
        "/app",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
    print(f"📂  Frontend served from: {FRONTEND_DIR}")
else:
    print(f"⚠️   No frontend/ folder found at {FRONTEND_DIR}")
    print("     Create it and put your HTML/CSS/JS files inside.")


# ── Pydantic models ────────────────────────────────────────────────────────────
class DiagnosisRequest(BaseModel):
    query:       str
    crop_filter: Optional[str] = None   # "Wheat", "Cotton", etc. or null = all
    language:    str = "both"           # "both" | "english" | "urdu"

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Yellow spots on wheat leaves spreading fast",
                "crop_filter": "Wheat",
                "language": "both",
            }
        }


class DiagnosisResponse(BaseModel):
    success:     bool
    response:    str
    query:       str
    crop_filter: Optional[str]
    language:    str
    engine_used: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root URL to the frontend app."""
    return RedirectResponse(url="/app/index.html")


@app.get("/health")
def health():
    """Health check — returns engine status."""
    return {
        "status":         "ok",
        "engine_loaded":  ENGINE_LOADED,
        "engine_error":   ENGINE_ERROR or None,
    }


@app.get("/status")
def status():
    """Full status — used by frontend api.js to show server badge."""
    return {
        "engine_loaded":   ENGINE_LOADED,
        "disease_records": 427,
        "crops":           14,
        "languages":       ["english", "urdu", "both"],
        "version":         "2.0.0",
    }


@app.get("/crops")
def list_crops():
    """Return list of supported crops."""
    return {
        "crops": [
            {"en": "Wheat",      "ur": "گندم"},
            {"en": "Cotton",     "ur": "کپاس"},
            {"en": "Rice",       "ur": "چاول"},
            {"en": "Sugarcane",  "ur": "گنا"},
            {"en": "Maize",      "ur": "مکئی"},
            {"en": "Groundnut",  "ur": "مونگ پھلی"},
            {"en": "Barley",     "ur": "جَو"},
            {"en": "Sorghum",    "ur": "جوار"},
            {"en": "Millet",     "ur": "باجرہ"},
            {"en": "Brassica",   "ur": "سرسوں"},
            {"en": "Gram",       "ur": "چنا"},
            {"en": "Coriander",  "ur": "دھنیا"},
            {"en": "Paddy",      "ur": "دھان"},
            {"en": "Lentil",     "ur": "مسور"},
        ]
    }


@app.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(req: DiagnosisRequest):
    """
    Main diagnosis endpoint.
    Accepts a symptom query, optional crop filter, and language preference.
    Returns structured bilingual disease diagnosis from the RAG engine.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not ENGINE_LOADED:
        raise HTTPException(
            status_code=503,
            detail=(
                f"RAG engine is not loaded. "
                f"Error: {ENGINE_ERROR or 'unknown'}. "
                "Check server logs and ensure rag_engine.py and .env are correct."
            ),
        )

    try:
        result = get_diagnosis(
            query=req.query.strip(),
            crop_filter=req.crop_filter or None,
            language=req.language,
        )
        return DiagnosisResponse(
            success=True,
            response=result,
            query=req.query,
            crop_filter=req.crop_filter,
            language=req.language,
            engine_used="gemini+chromadb",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Diagnosis failed: {exc}",
        )


# ── Dev entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fasal_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT / "src")],   # watch src/ for changes
    )
