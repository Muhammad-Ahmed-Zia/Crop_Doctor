"""
src/explore_datasets.py
═══════════════════════════════════════════════════════════════
FASAL DOCTOR — Phase 2, Day 1 | Step 3
Dataset Exploration & Mapping Script

Walks data/raw/ and produces:
  • Human-readable terminal report
  • data/processed/dataset_map.json

Run:
    python src/explore_datasets.py
═══════════════════════════════════════════════════════════════
"""

import os
import json
import sys
from pathlib import Path
from collections import defaultdict

# ── Try to import PIL for corrupt-image checking ──────────────
try:
    from PIL import Image, UnidentifiedImageError
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠  Pillow not installed — corrupt-image check skipped.")
    print("   Run: pip install pillow\n")

# ── Configuration ─────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent   # project root
RAW_DIR     = BASE_DIR / "data" / "raw"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "dataset_map.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

MIN_IMAGES   = 200    # below this → WARNING (too few)
MAX_IMAGES   = 5000   # above this → INFO (consider capping)

# ── Colour helpers (Windows-safe) ─────────────────────────────
try:
    import colorama
    colorama.init(autoreset=True)
    GREEN  = colorama.Fore.GREEN
    YELLOW = colorama.Fore.YELLOW
    RED    = colorama.Fore.RED
    CYAN   = colorama.Fore.CYAN
    BOLD   = colorama.Style.BRIGHT
    RESET  = colorama.Style.RESET_ALL
except ImportError:
    GREEN = YELLOW = RED = CYAN = BOLD = RESET = ""


# ─────────────────────────────────────────────────────────────
def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def count_images_in_dir(folder: Path) -> tuple[int, dict, int]:
    """Return (total_count, format_counts, corrupt_count)."""
    fmt_counts: dict[str, int] = defaultdict(int)
    total = 0
    corrupt = 0

    for f in folder.rglob("*"):
        if f.is_file() and is_image(f):
            ext = f.suffix.lower()
            fmt_counts[ext] += 1
            total += 1

            if PIL_AVAILABLE:
                try:
                    with Image.open(f) as img:
                        img.verify()
                except (UnidentifiedImageError, Exception):
                    corrupt += 1

    return total, dict(fmt_counts), corrupt


def get_status_symbol(count: int) -> str:
    if count < MIN_IMAGES:
        return f"{RED}⚠ TOO FEW{RESET}"
    if count > MAX_IMAGES:
        return f"{YELLOW}⚡ LARGE{RESET}"
    return f"{GREEN}✓{RESET}"


def get_status_text(count: int) -> str:
    if count < MIN_IMAGES:
        return "TOO_FEW"
    if count > MAX_IMAGES:
        return "LARGE"
    return "OK"


# ─────────────────────────────────────────────────────────────
def explore_crop(crop_path: Path) -> dict:
    """
    Explore a single crop folder.

    Handles two layouts:
      (A) Flat:   crop_folder/ClassName/images...
      (B) Split:  crop_folder/train|Training|test.../ClassName/images...
    """
    crop_name = crop_path.name
    result = {
        "crop": crop_name,
        "path": str(crop_path.relative_to(BASE_DIR)),
        "layout": None,
        "splits": {},
        "classes": {},
        "total_images": 0,
        "total_corrupt": 0,
        "formats": {},
        "warnings": [],
        "status": "OK",
    }

    children = [c for c in crop_path.iterdir() if c.is_dir()]
    if not children:
        result["status"] = "EMPTY"
        result["warnings"].append("No subfolders found")
        return result

    # ── Detect layout ─────────────────────────────────────────
    SPLIT_KEYWORDS = {"train", "training", "test", "testing",
                      "val", "validation", "valid"}

    first_child_name = children[0].name.lower()
    is_split_layout = any(
        any(kw in c.name.lower() for kw in SPLIT_KEYWORDS)
        for c in children
    )

    # ── Flat layout ───────────────────────────────────────────
    if not is_split_layout:
        result["layout"] = "flat"
        result["splits"]["all"] = {}
        for cls_dir in sorted(children):
            count, fmts, corrupt = count_images_in_dir(cls_dir)
            result["classes"][cls_dir.name] = {
                "count": count,
                "formats": fmts,
                "corrupt": corrupt,
                "status": get_status_text(count),
            }
            result["total_images"] += count
            result["total_corrupt"] += corrupt
            for ext, n in fmts.items():
                result["formats"][ext] = result["formats"].get(ext, 0) + n
            result["splits"]["all"][cls_dir.name] = count

    # ── Split layout ──────────────────────────────────────────
    else:
        result["layout"] = "split"
        merged_classes: dict[str, dict] = {}

        for split_dir in sorted(children):
            if not split_dir.is_dir():
                continue
            split_name = split_dir.name
            result["splits"][split_name] = {}

            for cls_dir in sorted(split_dir.iterdir()):
                if not cls_dir.is_dir():
                    continue
                count, fmts, corrupt = count_images_in_dir(cls_dir)
                cls = cls_dir.name
                result["splits"][split_name][cls] = count
                result["total_images"] += count
                result["total_corrupt"] += corrupt

                if cls not in merged_classes:
                    merged_classes[cls] = {"count": 0, "formats": {}, "corrupt": 0}
                merged_classes[cls]["count"] += count
                merged_classes[cls]["corrupt"] += corrupt
                for ext, n in fmts.items():
                    merged_classes[cls]["formats"][ext] = \
                        merged_classes[cls]["formats"].get(ext, 0) + n
                    result["formats"][ext] = result["formats"].get(ext, 0) + n

        for cls, data in merged_classes.items():
            result["classes"][cls] = {
                "count": data["count"],
                "formats": data["formats"],
                "corrupt": data["corrupt"],
                "status": get_status_text(data["count"]),
            }

    # ── Warnings & overall status ─────────────────────────────
    for cls, data in result["classes"].items():
        if data["count"] < MIN_IMAGES:
            result["warnings"].append(
                f"'{cls}' has only {data['count']} images — consider augmentation"
            )
            result["status"] = "NEEDS_ATTENTION"
        if data["count"] > MAX_IMAGES:
            result["warnings"].append(
                f"'{cls}' has {data['count']} images — consider capping at {MAX_IMAGES}"
            )

    if result["total_corrupt"] > 0:
        result["warnings"].append(
            f"{result['total_corrupt']} corrupt/unreadable image(s) detected"
        )
        result["status"] = "NEEDS_ATTENTION"

    if not result["classes"]:
        result["status"] = "EMPTY"
        result["warnings"].append("No class folders with images found")

    return result


# ─────────────────────────────────────────────────────────────
def print_crop_report(info: dict) -> None:
    crop     = info["crop"]
    path     = info["path"]
    classes  = info["classes"]
    total    = info["total_images"]
    corrupt  = info["total_corrupt"]
    layout   = info["layout"]
    warnings = info["warnings"]
    status   = info["status"]

    print(f"\n{BOLD}{CYAN}📁 {path}/{RESET}")
    print(f"   Layout : {layout or 'unknown'}")

    if not classes:
        print(f"   {RED}⚠  No classes found!{RESET}")
        for w in warnings:
            print(f"      • {YELLOW}{w}{RESET}")
        print(f"   STATUS: {RED}❌ Empty / Needs Investigation{RESET}")
        return

    # Tree-style class listing
    class_items = sorted(classes.items())
    for i, (cls_name, data) in enumerate(class_items):
        connector = "└──" if i == len(class_items) - 1 else "├──"
        sym = get_status_symbol(data["count"])
        fmts = ", ".join(data.get("formats", {}).keys()) or "—"
        corrupt_note = f" [{RED}{data['corrupt']} corrupt{RESET}]" if data["corrupt"] else ""
        print(f"   {connector} {cls_name:<40} {data['count']:>6} images  {sym}{corrupt_note}")

    print(f"   {'─'*65}")
    print(f"   TOTAL: {BOLD}{total:,} images{RESET} | {len(classes)} classes | layout: {layout}")

    if warnings:
        for w in warnings:
            print(f"   ⚠  {YELLOW}{w}{RESET}")

    if status == "OK":
        print(f"   STATUS: {GREEN}✅ Ready for training{RESET}")
    else:
        print(f"   STATUS: {YELLOW}⚠  Needs Attention{RESET}")


# ─────────────────────────────────────────────────────────────
def main():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  FASAL DOCTOR — DATASET EXPLORATION REPORT{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  Scanning: {RAW_DIR}")
    print(f"{'═'*60}")

    if not RAW_DIR.exists():
        print(f"{RED}ERROR: data/raw/ not found at {RAW_DIR}{RESET}")
        sys.exit(1)

    # ── Find all top-level crop folders ──────────────────────
    crop_folders = sorted(
        [d for d in RAW_DIR.iterdir() if d.is_dir() and d.name != "pdfs"],
        key=lambda p: p.name.lower()
    )

    if not crop_folders:
        print(f"{RED}No crop folders found in data/raw/{RESET}")
        sys.exit(1)

    all_results = []
    for crop_path in crop_folders:
        print(f"\n  🔍 Scanning {crop_path.name}...", end="", flush=True)
        info = explore_crop(crop_path)
        all_results.append(info)
        print(f" done ({info['total_images']:,} images)")

    # ── Print full report ─────────────────────────────────────
    print(f"\n\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  DETAILED REPORT{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    for info in all_results:
        print_crop_report(info)

    # ── Overall summary ───────────────────────────────────────
    total_crops   = len(all_results)
    total_classes = sum(len(r["classes"]) for r in all_results)
    total_images  = sum(r["total_images"] for r in all_results)
    total_corrupt = sum(r["total_corrupt"] for r in all_results)
    ready         = sum(1 for r in all_results if r["status"] == "OK")
    attention     = total_crops - ready

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  OVERALL SUMMARY{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  Total crops found    : {BOLD}{total_crops}{RESET}")
    print(f"  Total classes found  : {BOLD}{total_classes}{RESET}")
    print(f"  Total images found   : {BOLD}{total_images:,}{RESET}")
    print(f"  Corrupt images found : {RED if total_corrupt else GREEN}{total_corrupt}{RESET}")
    print(f"  Crops ready          : {GREEN}{ready}{RESET}")
    print(f"  Crops need attention : {YELLOW if attention else GREEN}{attention}{RESET}")

    # ── Format breakdown ─────────────────────────────────────
    all_fmts: dict[str, int] = defaultdict(int)
    for r in all_results:
        for ext, cnt in r.get("formats", {}).items():
            all_fmts[ext] += cnt
    if all_fmts:
        print(f"\n  Image formats detected:")
        for ext, cnt in sorted(all_fmts.items()):
            print(f"    {ext:<8}: {cnt:,}")

    print(f"{BOLD}{'═'*60}{RESET}\n")

    # ── Save JSON ────────────────────────────────────────────
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "summary": {
            "total_crops": total_crops,
            "total_classes": total_classes,
            "total_images": total_images,
            "total_corrupt": total_corrupt,
            "crops_ready": ready,
            "crops_need_attention": attention,
            "image_formats": dict(all_fmts),
        },
        "crops": all_results,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ Full report saved to: {OUTPUT_PATH}")
    print()


if __name__ == "__main__":
    main()
