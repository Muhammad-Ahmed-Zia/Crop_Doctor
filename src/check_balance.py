"""
src/check_balance.py — FASAL DOCTOR Phase 2 Day 1 Step 5
Analyses data/images/ for class imbalance.
Run: python src/check_balance.py
"""
import json, sys
from pathlib import Path

try:
    import colorama; colorama.init(autoreset=True)
    G=colorama.Fore.GREEN; Y=colorama.Fore.YELLOW; R=colorama.Fore.RED
    C=colorama.Fore.CYAN; B=colorama.Style.BRIGHT; X=colorama.Style.RESET_ALL
except ImportError:
    G=Y=R=C=B=X=""

BASE_DIR    = Path(__file__).resolve().parent.parent
IMAGES_DIR  = BASE_DIR / "data" / "images"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "balance_report.json"
IMG_EXTS    = {".jpg",".jpeg",".png",".bmp",".tiff",".tif",".webp"}
MIN_IMG     = 200
CAP_IMG     = 3000
IMBAL_RATIO = 3.0


def count_imgs(folder: Path) -> int:
    return sum(1 for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in IMG_EXTS)


def cls_status(n: int) -> tuple:
    if n < MIN_IMG:  return "⚠ TOO FEW", R
    if n > CAP_IMG:  return "⚡ LARGE", Y
    return "✅ OK", G


def analyse_crop(crop_dir: Path) -> dict:
    crop = crop_dir.name
    classes = {d.name: count_imgs(d) for d in sorted(crop_dir.iterdir()) if d.is_dir()}
    if not classes:
        return {"crop": crop, "classes": {}, "total": 0, "balance_ratio": None,
                "imbalanced": False, "training_ready": False,
                "recommendations": ["No classes found — run organize_images.py"]}
    counts = list(classes.values())
    total, mx, mn = sum(counts), max(counts), min(counts)
    ratio = round(mx / mn, 2) if mn else float("inf")
    imbal = ratio > IMBAL_RATIO
    ready = mn >= MIN_IMG
    per = {}
    recs = []
    if imbal:
        recs.append(f"Imbalanced ({ratio:.1f}x). Oversample smallest class.")
    for cls, n in classes.items():
        lbl, _ = cls_status(n)
        cr = []
        if n < MIN_IMG:  cr.append("Apply heavy augmentation")
        if n > CAP_IMG:  cr.append(f"Consider capping at {CAP_IMG}")
        per[cls] = {"count": n, "status": lbl, "recommendations": cr}
        recs.extend([f"{cls}: {r}" for r in cr])
    return {"crop": crop, "classes": per, "total": total,
            "min_class_count": mn, "max_class_count": mx,
            "balance_ratio": ratio, "imbalanced": imbal,
            "training_ready": ready,
            "recommendations": list(dict.fromkeys(recs))}


def print_table(info: dict):
    crop, classes, total = info["crop"], info["classes"], info["total"]
    ratio, ready, imbal  = info["balance_ratio"], info["training_ready"], info["imbalanced"]
    W = 24
    print(f"\n  {B}{C}{crop.upper()} Disease Classes:{X}")
    print(f"  ┌{'─'*(W+2)}┬{'─'*10}┬{'─'*14}┐")
    print(f"  │ {'Class':<{W}} │ {'Count':>8} │ {'Status':^12} │")
    print(f"  ├{'─'*(W+2)}┼{'─'*10}┼{'─'*14}┤")
    for cls, d in classes.items():
        lbl, col = cls_status(d["count"])
        print(f"  │ {cls:<{W}} │ {d['count']:>8,} │ {col}{lbl:^12}{X} │")
    print(f"  ├{'─'*(W+2)}┼{'─'*10}┼{'─'*14}┤")
    rs = f"{ratio:.1f}×" if ratio else "N/A"
    ic = R if imbal else G
    print(f"  │ {'TOTAL':<{W}} │ {total:>8,} │ {'':^12} │")
    print(f"  │ {'Balance ratio':<{W}} │ {rs:>8} │ {ic}{'IMBALANCED' if imbal else 'BALANCED':^12}{X} │")
    print(f"  │ {'Training ready':<{W}} │ {'':>8} │ {G if ready else R}{'YES' if ready else 'NO':^12}{X} │")
    print(f"  └{'─'*(W+2)}┴{'─'*10}┴{'─'*14}┘")
    for rec in info.get("recommendations", [])[:4]:
        print(f"    {Y}• {rec}{X}")


def main():
    print(f"\n{B}{'═'*60}{X}")
    print(f"{B}  FASAL DOCTOR — CLASS BALANCE REPORT{X}")
    print(f"{B}{'═'*60}{X}")
    if not IMAGES_DIR.exists():
        print(f"{R}ERROR: data/images/ not found. Run organize_images.py first.{X}")
        sys.exit(1)

    crop_dirs = sorted([d for d in IMAGES_DIR.iterdir() if d.is_dir()])
    results   = [analyse_crop(d) for d in crop_dirs]
    for r in results:
        print_table(r)

    ready  = [r for r in results if r["training_ready"]]
    imbal  = [r for r in results if r["imbalanced"]]
    grand  = sum(r["total"] for r in results)
    n_cls  = sum(len(r["classes"]) for r in results)

    print(f"\n{B}{'═'*60}{X}")
    print(f"{B}  OVERALL SUMMARY{X}")
    print(f"{B}{'═'*60}{X}")
    print(f"  Total crops    : {len(results)}")
    print(f"  Total classes  : {n_cls}")
    print(f"  Total images   : {grand:,}")
    print(f"  Training ready : {G}{len(ready)}{X}")
    print(f"  Need attention : {R if len(results)-len(ready) else G}{len(results)-len(ready)}{X}")
    print(f"  Imbalanced     : {Y if imbal else G}{len(imbal)}{X}")
    print(f"{B}{'═'*60}{X}\n")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "summary": {"total_crops": len(results), "total_classes": n_cls,
                     "total_images": grand, "ready_crops": len(ready),
                     "imbalanced_crops": len(imbal)},
        "thresholds": {"min_images": MIN_IMG, "cap": CAP_IMG, "imbalance_ratio": IMBAL_RATIO},
        "crops": results,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✅ Balance report saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
