"""
fasal_server.py — FastAPI bridge between the HTML frontend and the RAG engine.

Run from the PROJECT ROOT with:
    python -m uvicorn api.fasal_server:app --host 0.0.0.0 --port 8000 --reload

Frontend is auto-served at:  http://localhost:8000/app/
Or open frontend/index.html directly in a browser (set FASAL_API in api.js).
"""

import sys, os
from pathlib import Path

# Project root = two levels up from api/fasal_server.py
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

# ── Import RAG engine ──────────────────────────────────────────────────────────
try:
    from rag_engine import get_diagnosis, get_retriever
    get_retriever()          # warm up vectors on startup
    ENGINE_LOADED = True
except Exception as e:
    print(f"⚠️  RAG engine not loaded: {e}")
    ENGINE_LOADED = False

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fasal Doctor API",
    description="AI Crop Disease Diagnosis — PARC Pakistan + Gemini",
    version="2.0.0",
)

# Allow the HTML frontend (any origin in dev; tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the HTML frontend at /  (frontend files must be in ./frontend/)
frontend_dir = ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


# ── Models ─────────────────────────────────────────────────────────────────────
class DiagnosisRequest(BaseModel):
    query: str
    crop_filter: Optional[str] = None   # e.g. "Wheat"
    language: str = "both"              # "both" | "english" | "urdu"


class DiagnosisResponse(BaseModel):
    success: bool
    response: str
    query: str
    crop_filter: Optional[str]
    language: str
    engine_used: str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    """Redirect root URL to the HTML frontend."""
    return RedirectResponse(url="/app/index.html")


@app.get("/api")
def api_info():
    """JSON info endpoint (previously at root)."""
    return {
        "name": "Fasal Doctor API",
        "version": "2.0.0",
        "engine": "loaded" if ENGINE_LOADED else "unavailable",
        "frontend": "http://localhost:8000/app/",
        "endpoints": {
            "POST /diagnose": "Run crop disease diagnosis",
            "GET  /status":   "Check engine status",
            "GET  /crops":    "List supported crops",
        }
    }


@app.get("/status")
def status():
    return {
        "engine_loaded": ENGINE_LOADED,
        "disease_records": 427,
        "crops": 14,
        "languages": ["english", "urdu", "both"],
    }


@app.get("/crops")
def list_crops():
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
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not ENGINE_LOADED:
        # Return a clearly marked fallback so the frontend shows a warning
        raise HTTPException(
            status_code=503,
            detail="RAG engine is not loaded. Check server logs."
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


# ── Dev entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    # Run as: python api/fasal_server.py  (from project root)
    uvicorn.run("api.fasal_server:app", host="0.0.0.0", port=8000, reload=True)
