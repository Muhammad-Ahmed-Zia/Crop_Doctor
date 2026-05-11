"""
app.py — HuggingFace Spaces entry point for Fasal Doctor.
Streamlit on HF Spaces requires app.py at the project root with sdk: streamlit.
This file configures paths then runs the real UI in app/streamlit_app.py.
"""
import sys, os, runpy
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))   # so 'from rag_engine import ...' works
os.chdir(ROOT)                          # all relative paths (data/, models/) resolve correctly

# ── Auto-build ChromaDB if missing (first deploy on HF Spaces) ─────────────
if not Path("data/chroma_db").exists():
    print("ChromaDB not found — building embeddings (this takes ~3 min on first run)...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "src/embedder.py"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("⚠️  Embedder exited with error — check logs above.")

# ── Launch the Streamlit UI ─────────────────────────────────────────────────
# runpy.run_path executes the module as __main__ so Streamlit sees it correctly.
runpy.run_path(str(ROOT / "app" / "streamlit_app.py"), run_name="__main__")
