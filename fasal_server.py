"""
fasal_server.py  —  Fasal Doctor v2.0 Backend
═══════════════════════════════════════════════
This is a NEW file. It REPLACES the old Streamlit UI (streamlit_app.py).

WHAT IT DOES:
  - Serves the HTML frontend at  http://localhost:8000/app/
  - Exposes a REST API that diagnosis.html calls to run AI diagnosis
  - Wraps your existing rag_engine.py — zero changes to the RAG logic

WHERE TO PUT THIS FILE:
  fasal-doctor/
  ├── fasal_server.py       ← HERE (project root)
  ├── frontend/             ← HTML/JS files
  ├── src/
  │   ├── rag_engine.py     ← untouched
  │   └── embedder.py       ← untouched
  ├── app/
  │   └── streamlit_app.py  ← DEPRECATED, keep for reference, do not delete
  └── .env                  ← GOOGLE_API_KEY=your_key

HOW TO RUN:
  pip install fastapi "uvicorn[standard]" python-dotenv
  uvicorn fasal_server:app --host 0.0.0.0 --port 8000 --reload

URLs after startup:
  Frontend  →  http://localhost:8000/app/index.html
  API docs  →  http://localhost:8000/api/docs
  Status    →  http://localhost:8000/status
"""

import sys
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent   # project root: fasal-doctor/
SRC  = ROOT / "src"                      # fasal-doctor/src/

# Add src/ to sys.path BEFORE importing rag_engine
sys.path.insert(0, str(SRC))

# Change to project root so ChromaDB relative paths resolve correctly
os.chdir(ROOT)

# ── Load .env ──────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── FastAPI ────────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from typing import Optional, Callable

# ── Load RAG Engine ────────────────────────────────────────────────────────────
ENGINE_LOADED  = False
ENGINE_ERROR   = ""
RECORD_COUNT   = 671   # updated dynamically below if engine loads

try:
    from rag_engine import get_diagnosis, get_retriever
    print("🔄  Warming up ChromaDB vectors...")
    _col, _ = get_retriever()
    RECORD_COUNT  = _col.count()
    ENGINE_LOADED = True
    print(f"✅  RAG engine ready — {RECORD_COUNT} disease records loaded")
except Exception as exc:
    ENGINE_ERROR = str(exc)
    print(f"⚠️   RAG engine failed to load: {exc}")
    print("     Server running in demo mode — HTML frontend still accessible")

# ── Create App ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fasal Doctor API",
    description="AI Crop Disease Diagnosis — PARC Pakistan × Google Gemini × ChromaDB",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allows the HTML frontend (any origin) to call this API.
# For production, replace ["*"] with your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# ── No-Cache Middleware for HTML ───────────────────────────────────────────────
# Prevents the browser from serving stale cached HTML when the frontend is updated.
@app.middleware("http")
async def no_cache_html(request: Request, call_next: Callable) -> Response:
    response = await call_next(request)
    if request.url.path.endswith(".html") or request.url.path in ("/", "/app/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# ── Serve HTML Frontend ────────────────────────────────────────────────────────
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount(
        "/app",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
    print(f"📂  Frontend served at: http://localhost:8000/app/index.html")
else:
    print(f"⚠️   No frontend/ folder found at {FRONTEND_DIR}")
    print("     Copy your HTML files into fasal-doctor/frontend/")

# ── Request / Response Models ──────────────────────────────────────────────────
class DiagnosisRequest(BaseModel):
    query:       str
    crop_filter: Optional[str] = None   # "Wheat" | "Cotton" | ... | None = all crops
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
def root():
    """Redirect / to the frontend home page."""
    return RedirectResponse(url="/app/index.html")


@app.get("/health")
def health():
    """Quick health check."""
    return {
        "status": "ok",
        "engine_loaded": ENGINE_LOADED,
        "engine_error": ENGINE_ERROR or None,
    }


@app.get("/status")
def status():
    """
    Full status endpoint — called by diagnosis.html on page load
    to show the green/amber AI engine badge in the sidebar.
    """
    return {
        "engine_loaded":   ENGINE_LOADED,
        "disease_records": RECORD_COUNT,   # live count from ChromaDB
        "crops":           19,             # number of crops covered
        "languages":       ["english", "urdu", "both"],
        "version":         "2.0.0",
    }


@app.get("/crops")
def list_crops():
    """Return all 19 supported crops with English and Urdu names."""
    return {
        "crops": [
            {"en": "Wheat",      "ur": "گندم"},
            {"en": "Cotton",     "ur": "کپاس"},
            {"en": "Rice",       "ur": "چاول"},
            {"en": "Sugarcane",  "ur": "گنا"},
            {"en": "Maize",      "ur": "مکئی"},
            {"en": "Brassica",   "ur": "سرسوں"},
            {"en": "Gram",       "ur": "چنا"},
            {"en": "Groundnut",  "ur": "مونگ پھلی"},
            {"en": "Barley",     "ur": "جَو"},
            {"en": "Lentil",     "ur": "مسور"},
            {"en": "Sorghum",    "ur": "جوار"},
            {"en": "Millet",     "ur": "باجرہ"},
            {"en": "Coriander",  "ur": "دھنیا"},
            {"en": "Paddy",      "ur": "دھان"},
            {"en": "Vegetables", "ur": "سبزیاں"},
            {"en": "Tomato",     "ur": "ٹماٹر"},
            {"en": "Potato",     "ur": "آلو"},
            {"en": "Onion",      "ur": "پیاز"},
            {"en": "Chilies",    "ur": "مرچ"},
        ]
    }


@app.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(req: DiagnosisRequest):
    """
    Main AI diagnosis endpoint.

    Takes symptom description in Urdu or English, optional crop filter,
    and language preference. Returns a structured bilingual diagnosis
    from the RAG engine (ChromaDB vector search + Google Gemini).

    The response text is formatted as:
        **Disease Name:** ...
        **بیماری کا نام:** ...
        **Affected Crop:** ...
        **Symptoms:**
        **English:** ...
        **اردو:** ...
        **Spray Chemical:** ...
        **Pakistan Brand:** ...
        **Dose per Acre:** ...
        **Spray Timing:** ...
        **Severity:** ...
        **Yield Loss:** ...
        ---SAFETY WARNING---
        ... Urdu text ...
        ---
        ---BIOLOGICAL CONTROL---
        ... text ...
        ---
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not ENGINE_LOADED:
        raise HTTPException(
            status_code=503,
            detail=(
                f"RAG engine is not available. "
                f"Error: {ENGINE_ERROR or 'unknown'}. "
                "Check that GOOGLE_API_KEY is set in .env and ChromaDB is built."
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


# ── Dev Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fasal_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(SRC)],  # watch src/ for rag_engine changes
    )
