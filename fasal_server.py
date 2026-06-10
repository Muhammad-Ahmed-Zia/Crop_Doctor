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
from contextlib import asynccontextmanager

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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

# ── Engine state (populated by lifespan startup) ───────────────────────────────
ENGINE_LOADED    = False
ENGINE_ERROR     = ""
_get_diagnosis   = None   # set during lifespan startup

def load_engine_background():
    global ENGINE_LOADED, ENGINE_ERROR, _get_diagnosis
    try:
        from rag_engine import get_diagnosis, get_retriever
        print("🔄  Warming up ChromaDB vectors...")
        get_retriever()
        _get_diagnosis = get_diagnosis   # store at module level for route handlers
        ENGINE_LOADED = True
        print("✅  RAG engine ready — 671 disease records loaded")
    except Exception as exc:
        ENGINE_ERROR = str(exc)
        print(f"⚠️   RAG engine failed to load: {exc}")
        print("     Server running in demo mode — HTML frontend still accessible")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the RAG engine once when the server worker starts (not the reloader)."""
    import threading
    from pathlib import Path
    import subprocess
    import sys
    
    # Auto-process logo_square.jpg into transparent logo.png
    try:
        from PIL import Image, ImageDraw
        base_dir = Path(__file__).resolve().parent
        img_path = base_dir / "frontend" / "images" / "logo_square.jpg"
        output_path = base_dir / "frontend" / "images" / "logo.png"
        
        if img_path.exists():
            print(f"🔄 Processing logo from {img_path} to produce transparent PNG...")
            img = Image.open(img_path).convert("RGBA")
            width, height = img.size
            pixels = img.load()
            
            # Inspect corner pixels to detect JPEG background noise level
            corners = [pixels[0, 0], pixels[width - 1, 0], pixels[0, height - 1], pixels[width - 1, height - 1]]
            max_bg = max(max(c[0], c[1], c[2]) for c in corners)
            threshold = max(max_bg + 20, 50)  # Dynamic threshold: noise + margin, min 50
            print(f"🔍 Logo processor: max corner noise={max_bg}, using threshold={threshold}")
            
            # Find bounding box of foreground pixels using threshold
            left, top, right, bottom = width, height, 0, 0
            for y in range(height):
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    if r > threshold or g > threshold or b > threshold:
                        if x < left: left = x
                        if y < top: top = y
                        if x > right: right = x
                        if y > bottom: bottom = y
            
            if left < right and top < bottom:
                # Shave off 4 pixels on each side to completely eliminate any black border transition line
                shave = 4
                left_cropped = left + shave
                top_cropped = top + shave
                right_cropped = right - shave
                bottom_cropped = bottom - shave
                
                # Double check bounds
                if left_cropped < right_cropped and top_cropped < bottom_cropped:
                    cropped = img.crop((left_cropped, top_cropped, right_cropped + 1, bottom_cropped + 1))
                else:
                    cropped = img.crop((left, top, right + 1, bottom + 1))
                
                # Make it a perfect square
                w, h = cropped.size
                size = max(w, h)
                square_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                square_img.paste(cropped, ((size - w) // 2, (size - h) // 2))
                
                # Apply rounded rectangle mask
                radius = int(size * 0.22)
                mask = Image.new("L", (size, size), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, size - 1, size - 1), radius, fill=255)
                
                # Combine mask
                final_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                final_img.paste(square_img, (0, 0), mask=mask)
                
                # Save as PNG
                final_img.save(output_path, "PNG")
                print(f"✅ Transparent logo saved to: {output_path} (size={size}x{size})")
            else:
                print("⚠️ Failed to detect logo boundaries inside logo_square.jpg.")
        else:
            print(f"⚠️ logo_square.jpg not found at {img_path}")
    except Exception as e:
        print(f"⚠️ Error processing logo image: {e}")

    # Auto-embed ChromaDB if it doesn't exist (e.g. first deploy on cloud)
    chroma_path = Path("data/chroma_db")
    if not (chroma_path / "chroma.sqlite3").exists():
        print("🔄 ChromaDB database not found or incomplete. Running embedder.py to build it (takes ~3 minutes)...")
        try:
            subprocess.run(
                [sys.executable, "src/embedder.py"],
                check=True
            )
            print("✅ ChromaDB database built successfully!")
        except Exception as embed_err:
            print(f"❌ Failed to run embedder.py: {embed_err}")
            
    # Start engine loading in a background thread so the server binds to port immediately
    threading.Thread(target=load_engine_background, daemon=True).start()
    print("🚀 Background engine loader thread started. FastAPI server starting up...")
    yield  # server runs here
    # (cleanup if needed on shutdown)

# ── Create App ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fasal Doctor API",
    description="AI Crop Disease Diagnosis — PARC Pakistan × Google Gemini × ChromaDB",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        "https://crop-doctor-tau.vercel.app",
        "https://ahmed-zia-fasal-doctor.hf.space",
        "*",   # fallback — remove in production if you want strict CORS
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

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
        "disease_records": 671,    # PARC Pakistan database size
        "crops":           19,     # number of crops covered
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
        result = _get_diagnosis(
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
