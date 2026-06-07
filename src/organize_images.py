"""
src/organize_images.py
═══════════════════════════════════════════════════════════════
FASAL DOCTOR — Phase 2, Day 1 | Step 4
Dataset Organization Script

Reads data/processed/dataset_map.json (from explore_datasets.py)
then COPIES images into a clean, standardised structure:

    data/images/
        wheat/yellow_rust/ ...
        cotton/grey_mildew/ ...
        ...

Run AFTER explore_datasets.py:
    python src/organize_images.py

Add data/images/ to .gitignore — it is too large for GitHub.
═══════════════════════════════════════════════════════════════
"""

import json
import shutil
import sys
from pathlib import Path
from collections import defaultdict

# ── Colour helpers ────────────────────────────────────────────
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

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
RAW_DIR    = BASE_DIR / "data" / "raw"
IMAGES_DIR = BASE_DIR / "data" / "images"
MAP_PATH   = BASE_DIR / "data" / "processed" / "dataset_map.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# ─────────────────────────────────────────────────────────────
# MAPPING DEFINITIONS
# Each crop entry describes:
#   source_root  : path relative to data/raw/
#   splits       : list of sub-folders that contain class dirs
#                  (empty list → flat layout, class dirs are direct children)
#   class_map    : {exact_source_folder_name: target_class_name}
#                  Keys are CASE-SENSITIVE folder names as found on disk.
#
# NOTE ON COTTON:
#   The dataset on disk (data/raw/Cotton/) is the saeedazfar *customized*
#   cotton dataset, but the actual classes present are:
#     Aphids, Army worm, Bacterial blight, Cotton Boll Rot,
#     Green Cotton Boll, Healthy, Powdery mildew, Target spot
#   These do NOT match the grey_mildew/fusarium_wilt target list.
#   We map what is available and note this mismatch.
#
# NOTE ON MAIZE:
#   data/raw/Maize/ contains images from two merged sources
#   (PlantVillage + another dataset).  We only take the 4
#   canonical PlantVillage classes and ignore pest/ear-rot classes.
# ─────────────────────────────────────────────────────────────

CROP_CONFIGS: list[dict] = [
    # ── WHEAT ─────────────────────────────────────────────────
    {
        "crop": "wheat",
        "source_root": "Wheat",
        "splits": [],          # flat layout
        "class_map": {
            "Wheat___Yellow_Rust":    "yellow_rust",
            "Wheat Brown leaf Rust":  "brown_rust",
            "Wheat black rust":       "brown_rust",   # merge into brown_rust
            "Wheat leaf blight":      "leaf_blight",
            "Wheat scab":             "leaf_blight",  # merge into leaf_blight
            "Wheat powdery mildew":   "powdery_mildew",
            "Wheat aphid":            "aphid",
            "Wheat mite":             "mite",
            "Wheat Stem fly":         "stem_fly",
        },
        "skip_classes": [],
    },

    # ── COTTON ────────────────────────────────────────────────
    # Classes on disk differ from expected — map what exists.
    {
        "crop": "cotton",
        "source_root": "Cotton",
        "splits": ["Cotton-Disease-Training", "Cotton-Disease-Validation"],
        "class_map": {
            # Training split class names
            "Aphids":             "aphids",
            "Army worm":          "army_worm",
            "Bacterial blight":   "bacterial_blight",
            "Cotton Boll Rot":    "boll_rot",
            "Green Cotton Boll":  "green_boll",
            "Healthy":            "healthy",
            "Powdery mildew":     "powdery_mildew",
            "Target spot":        "target_spot",
            # Validation split may use slightly different names
            "Aphids edited":          "aphids",
            "Army worm edited":       "army_worm",
            "Bacterial Blight edited":"bacterial_blight",
            "Cotton Boll rot":        "boll_rot",
            "Healthy leaf edited":    "healthy",
            "Powdery Mildew Edited":  "powdery_mildew",
            "Target spot edited":     "target_spot",
        },
        "skip_classes": [],
    },

    # ── RICE ──────────────────────────────────────────────────
    {
        "crop": "rice",
        "source_root": "Rice",
        "splits": [],          # flat layout
        "class_map": {
            "Bacterialblight": "bacterial_blight",
            "Brownspot":       "brown_spot",
            "Leafsmut":        "leaf_smut",
            # If a Healthy folder appears
            "Healthy":         "healthy",
        },
        "skip_classes": [],
    },

    # ── SUGARCANE ─────────────────────────────────────────────
    {
        "crop": "sugarcane",
        "source_root": "Sugarcane",
        "splits": [],          # flat layout
        "class_map": {
            "Healthy": "healthy",
            "Mosaic":  "mosaic",
            "RedRot":  "red_rot",
            "Rust":    "rust",
            "Yellow":  "yellow",
        },
        "skip_classes": [],
    },

    # ── MAIZE ─────────────────────────────────────────────────
    # Only copy the 4 canonical PlantVillage classes; skip pest classes.
    {
        "crop": "maize",
        "source_root": "Maize",
        "splits": [],          # flat layout
        "class_map": {
            "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot":
                "gray_leaf_spot",
            "Corn_(maize)___Common_rust_":
                "common_rust",
            "Corn_(maize)___Northern_Leaf_Blight":
                "northern_blight",
            "Corn_(maize)___healthy":
                "healthy",
            # Second source duplicates (flat names)
            "Common_Rust":   "common_rust",
            "Gray_Leaf_Spot":"gray_leaf_spot",
            "Blight":        "northern_blight",
            "Healthy":       "healthy",
        },
        "skip_classes": [
            "maize ear rot",
            "maize fall armyworm",
            "maize stem borer",
        ],
    },

    # ── POTATO ────────────────────────────────────────────────
    {
        "crop": "potato",
        "source_root": "potato",
        "splits": ["Training", "Validation", "Testing"],
        "class_map": {
            "Early_Blight": "early_blight",
            "Late_Blight":  "late_blight",
            "Healthy":      "healthy",
        },
        "skip_classes": [],
    },

    # ── TOMATO ────────────────────────────────────────────────
    {
        "crop": "tomato",
        "source_root": "tomato",
        "splits": ["train", "val", "test"],
        "class_map": {
            "Early_blight":          "early_blight",
            "Late_blight":           "late_blight",
            "Healthy":               "healthy",
            "Leaf Miner":            "leaf_miner",
            "Magnesium Deficiency":  "magnesium_deficiency",
            "Nitrogen Deficiency":   "nitrogen_deficiency",
            "Pottassium Deficiency": "potassium_deficiency",
            "Spotted Wilt Virus":    "spotted_wilt_virus",
        },
        "skip_classes": [],
    },
]


# ─────────────────────────────────────────────────────────────
def copy_images(src_dir: Path, dst_dir: Path) -> int:
    """Copy all images from src_dir to dst_dir. Returns count copied."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for f in src_dir.rglob("*"):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            # Deduplicate: if file with same name exists, add numeric suffix
            dst_file = dst_dir / f.name
            if dst_file.exists():
                stem = f.stem
                suffix = f.suffix
                counter = 1
                while dst_file.exists():
                    dst_file = dst_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            shutil.copy2(f, dst_file)
            copied += 1
    return copied


def get_case_insensitive(class_map: dict, key: str):
    """Try exact match first, then case-insensitive match."""
    if key in class_map:
        return class_map[key]
    key_lower = key.lower()
    for k, v in class_map.items():
        if k.lower() == key_lower:
            return v
    return None


# ─────────────────────────────────────────────────────────────
def organize_crop(config: dict) -> dict:
    crop        = config["crop"]
    source_root = RAW_DIR / config["source_root"]
    splits      = config["splits"]
    class_map   = config["class_map"]
    skip_set    = {s.lower() for s in config.get("skip_classes", [])}

    summary = {
        "crop": crop,
        "classes": {},
        "skipped": [],
        "unmapped": [],
        "total_copied": 0,
    }

    if not source_root.exists():
        print(f"  {RED}⚠  Source not found: {source_root}{RESET}")
        summary["error"] = f"Source folder not found: {source_root}"
        return summary

    # ── Collect (source_class_dir, target_class_name) pairs ──
    pairs: list[tuple[Path, str]] = []

    if splits:
        # Split layout: iterate each split sub-folder
        for split_name in splits:
            split_dir = source_root / split_name
            if not split_dir.exists():
                # Try case-insensitive search
                for child in source_root.iterdir():
                    if child.is_dir() and child.name.lower() == split_name.lower():
                        split_dir = child
                        break
                else:
                    continue

            for cls_dir in sorted(split_dir.iterdir()):
                if not cls_dir.is_dir():
                    continue
                if cls_dir.name.lower() in skip_set:
                    summary["skipped"].append(cls_dir.name)
                    continue
                target = get_case_insensitive(class_map, cls_dir.name)
                if target is None:
                    summary["unmapped"].append(f"{split_name}/{cls_dir.name}")
                    continue
                pairs.append((cls_dir, target))
    else:
        # Flat layout: class dirs are direct children of source_root
        for cls_dir in sorted(source_root.iterdir()):
            if not cls_dir.is_dir():
                continue
            if cls_dir.name.lower() in skip_set:
                summary["skipped"].append(cls_dir.name)
                continue
            target = get_case_insensitive(class_map, cls_dir.name)
            if target is None:
                summary["unmapped"].append(cls_dir.name)
                continue
            pairs.append((cls_dir, target))

    # ── Copy ──────────────────────────────────────────────────
    for src_cls_dir, target_cls in pairs:
        dst = IMAGES_DIR / crop / target_cls
        n = copy_images(src_cls_dir, dst)
        if target_cls not in summary["classes"]:
            summary["classes"][target_cls] = 0
        summary["classes"][target_cls] += n
        summary["total_copied"] += n

    return summary


# ─────────────────────────────────────────────────────────────
def update_gitignore():
    gitignore = BASE_DIR / ".gitignore"
    entries = ["data/images/", "models/*.h5", "models/*.keras"]
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        additions = []
        for entry in entries:
            if entry not in content:
                additions.append(entry)
        if additions:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write("\n# Phase 2 — large binary/data files\n")
                for e in additions:
                    f.write(f"{e}\n")
            print(f"  ✅ Added to .gitignore: {', '.join(additions)}")
    else:
        print(f"  {YELLOW}⚠  .gitignore not found — please add entries manually{RESET}")


# ─────────────────────────────────────────────────────────────
def main():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  FASAL DOCTOR — ORGANIZE IMAGES{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  Source : {RAW_DIR}")
    print(f"  Target : {IMAGES_DIR}")
    print(f"{'═'*60}\n")

    # ── Check dataset_map.json ────────────────────────────────
    if not MAP_PATH.exists():
        print(f"{YELLOW}⚠  dataset_map.json not found at {MAP_PATH}")
        print(f"   Run explore_datasets.py first.{RESET}")
        print(f"   Proceeding with built-in config anyway...\n")
    else:
        print(f"  ✅ Found dataset_map.json")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    all_summaries = []
    grand_total = 0

    for config in CROP_CONFIGS:
        crop = config["crop"]
        print(f"\n  📦 Organizing {BOLD}{crop.upper()}{RESET}...")
        summary = organize_crop(config)
        all_summaries.append(summary)

        if "error" in summary:
            print(f"     {RED}ERROR: {summary['error']}{RESET}")
            continue

        for cls, count in sorted(summary["classes"].items()):
            status = f"{GREEN}✓{RESET}" if count >= 200 else f"{RED}⚠{RESET}"
            print(f"     {crop}/{cls:<35} {count:>6} images {status}")

        if summary["skipped"]:
            print(f"     {YELLOW}Skipped classes: {', '.join(set(summary['skipped']))}{RESET}")
        if summary["unmapped"]:
            print(f"     {RED}Unmapped (check class_map): {', '.join(set(summary['unmapped']))}{RESET}")

        total = summary["total_copied"]
        grand_total += total
        print(f"     {'─'*50}")
        print(f"     TOTAL copied: {BOLD}{total:,}{RESET}")

    # ── Final summary ─────────────────────────────────────────
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  FINAL SUMMARY{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    for s in all_summaries:
        crop  = s["crop"]
        total = s.get("total_copied", 0)
        n_cls = len(s.get("classes", {}))
        ok    = f"{GREEN}✅{RESET}" if total > 0 else f"{RED}❌{RESET}"
        print(f"  {ok} {crop:<12} {n_cls} classes  {total:>7,} images")

    print(f"\n  {'─'*40}")
    print(f"  Grand total: {BOLD}{grand_total:,} images{RESET}")
    print(f"  Output dir : {IMAGES_DIR}")
    print(f"{BOLD}{'═'*60}{RESET}\n")

    # ── Update .gitignore ─────────────────────────────────────
    update_gitignore()

    # ── Save organize summary ─────────────────────────────────
    out_path = BASE_DIR / "data" / "processed" / "organize_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ Organize summary saved to: {out_path}")


if __name__ == "__main__":
    main()
