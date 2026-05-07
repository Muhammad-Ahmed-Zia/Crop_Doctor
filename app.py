import sys, os
from pathlib import Path
import subprocess

# Configure paths for HuggingFace Spaces
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

# If ChromaDB does not exist, build embeddings automatically
if not Path("data/chroma_db").exists():
    print("ChromaDB not found. Building embeddings...")
    subprocess.run(["python", "src/embedder.py"], check=True)

# Import and run the Streamlit UI
import app.streamlit_app
