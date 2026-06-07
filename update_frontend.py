"""
update_frontend.py — Copy all Fasal Doctor frontend files to project
=====================================================================
Run from your project root:   python update_frontend.py

This script copies the new HTML/JS files from wherever you downloaded
them into the correct frontend/ folder inside your fasal-doctor project.

Works on Windows, Mac, and Linux.
"""

import os
import sys
import shutil
from pathlib import Path

# ── WHERE ARE THE DOWNLOADED FILES? ───────────────────────────────────────────
# The script tries these locations in order.
# Add your own path at the top of this list if needed.

POSSIBLE_SOURCES = [
    Path.home() / "Downloads" / "outputs",       # Windows: C:\Users\You\Downloads\outputs
    Path.home() / "Downloads",                    # Windows: C:\Users\You\Downloads (if files here)
    Path(__file__).parent / "outputs",            # Same folder as this script
    Path(__file__).parent,                        # Project root itself
]

# ── FILES TO COPY ──────────────────────────────────────────────────────────────
FRONTEND_FILES = [
    "index.html",
    "crops.html",
    "diagnosis.html",
    "reviews.html",
    "about.html",
    "api.js",
    "search-data.js",
]

BACKEND_FILES = [
    "fasal_server.py",
    "download_images.py",
]

# ── PROJECT ROOT ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

print("\n🌾 Fasal Doctor — Frontend File Updater")
print("=" * 52)
print(f"Project root : {PROJECT_ROOT}")
print(f"Frontend dir : {FRONTEND_DIR}\n")

# ── FIND SOURCE FOLDER ─────────────────────────────────────────────────────────
source = None
for candidate in POSSIBLE_SOURCES:
    if (candidate / "index.html").exists() and (candidate / "crops.html").exists():
        source = candidate
        print(f"✅  Found new files at: {source}")
        break

if not source:
    print("❌  Could not auto-find the downloaded files.")
    print("\nPlease enter the full path to your downloaded files folder:")
    print("(This is the folder containing index.html, crops.html, etc.)")
    entered = input("Path: ").strip().strip('"')
    source = Path(entered)
    if not source.exists():
        print(f"❌  Folder not found: {source}")
        sys.exit(1)

# ── CREATE FRONTEND DIR ────────────────────────────────────────────────────────
FRONTEND_DIR.mkdir(exist_ok=True)

# ── COPY FILES ─────────────────────────────────────────────────────────────────
print("\nCopying frontend files to frontend/ ...")
ok = 0
fail = 0

for fname in FRONTEND_FILES:
    src = source / fname
    dst = FRONTEND_DIR / fname
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  ✅  {fname}")
        ok += 1
    else:
        print(f"  ❌  {fname}  (not found in {source})")
        fail += 1

print("\nCopying backend files to project root ...")
for fname in BACKEND_FILES:
    src = source / fname
    dst = PROJECT_ROOT / fname
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  ✅  {fname}")
        ok += 1
    else:
        print(f"  ⚠️   {fname}  (not found — skipping)")

# ── CHECK README ───────────────────────────────────────────────────────────────
readme_src = source / "README.md"
if readme_src.exists():
    shutil.copy2(readme_src, PROJECT_ROOT / "README.md")
    print(f"  ✅  README.md")

# ── SUMMARY ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 52)
print(f"✅  {ok} files copied successfully")
if fail:
    print(f"❌  {fail} files missing from source")

print("""
Next steps:
  1. Download images (run once):
     python download_images.py

  2. Start the AI backend:
     uvicorn fasal_server:app --host 0.0.0.0 --port 8000 --reload

  3. Open in browser:
     http://localhost:8000/app/index.html

  OR open frontend/index.html directly for demo mode.
""")

# ── VERIFY ALL PAGES USE NEW TAILWIND DESIGN ───────────────────────────────────
print("Verifying pages have the new Tailwind design...")
for fname in FRONTEND_FILES:
    if fname.endswith(".html"):
        fpath = FRONTEND_DIR / fname
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            has_tailwind = "tailwindcss.com" in content
            has_syne = "Syne" in content
            status = "✅ NEW" if (has_tailwind and has_syne) else "❌ OLD (needs replacing)"
            print(f"  {fname:<22} {status}")
        else:
            print(f"  {fname:<22} ❌ FILE MISSING")

print("\nDone! 🌾\n")
