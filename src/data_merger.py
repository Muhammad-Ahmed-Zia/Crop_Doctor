"""
FASAL DOCTOR — Data Merger (STEP 2)
=====================================
Merges all extracted JSON files into one clean master dataset:
  - data/processed/extracted.json       (rich schema, 5 demo records)
  - data/processed/parc_diseases.json   (PARC book, 400-500 records)
  - Any other *.json files in data/processed/ (e.g. scraped.json)

Actions:
  1. Normalises both schemas into a single unified schema
  2. Deduplicates by (crop_name_en + disease_name_en) pair
     — keeps the richer record when duplicates found
  3. Filters out junk records (no disease name, no symptoms)
  4. Assigns sequential IDs: PK-001, PK-002 ...
  5. Saves to data/processed/master_dataset.json

Usage:
    python src/data_merger.py
    python src/data_merger.py --verbose
"""

import json, os, re, sys, argparse
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# ── Primary crop names of interest for Pakistan ───────────────────────────
MAJOR_CROPS = {
    "wheat", "cotton", "rice", "paddy", "sugarcane", "maize", "corn",
    "barley", "potato", "tomato", "mango", "onion", "chickpea",
    "lentil", "mustard", "brassica", "sunflower", "soybean", "groundnut",
    "banana", "citrus", "apple", "grape", "chillies", "sorghum",
    "millet", "castor", "safflower", "vegetables", "fruits",
}

# Junk/noise values that mean "nothing useful here"
JUNK_VALUES = {
    None, "", "not specified", "not mentioned", "n/a", "unknown",
    "consult agronomist", "not explicitly detailed", "not explicitly mentioned",
}


def _clean(val) -> str:
    """Strip and normalise a string value."""
    if val is None:
        return ""
    return str(val).strip()


def _is_junk(val) -> bool:
    return _clean(val).lower() in JUNK_VALUES


def _richness(rec: dict) -> int:
    """Count non-junk filled fields — used to prefer richer duplicates."""
    score = 0
    for k, v in rec.items():
        if k in ("id", "source", "source_page", "data_source"):
            continue
        if not _is_junk(v):
            score += 1
    return score


# ── Schema normalisers ────────────────────────────────────────────────────

def _norm_parc(r: dict) -> dict:
    """
    Normalise a PARC-schema record into the unified schema.
    PARC fields: crop_name, disease_name_en, disease_name_urdu,
                 symptoms_en, affected_part, disease_stage,
                 recommended_spray_en, spray_dosage, spray_timing,
                 season, source, source_page
    """
    crop = _clean(r.get("crop_name", ""))
    return {
        # Core identifiers
        "id":                   "",          # assigned later
        "crop_name_en":         crop,
        "crop_name_ur":         "",          # filled by urdu_enricher
        "disease_name_en":      _clean(r.get("disease_name_en", "")),
        "disease_name_ur":      _clean(r.get("disease_name_urdu", "")),

        # Pathology
        "pathogen_type":        "",
        "symptoms_en":          _clean(r.get("symptoms_en", "")),
        "symptoms_ur":          "",
        "affected_part":        _clean(r.get("affected_part", "")),
        "disease_stage":        _clean(r.get("disease_stage", "")),

        # Geography / season
        "season":               _clean(r.get("season", "")),
        "region_pakistan":      "Pakistan",
        "climate_trigger":      "",

        # Severity
        "severity_level":       "",

        # Treatment
        "spray_chemical_en":    _clean(r.get("recommended_spray_en", "")),
        "brand_name_pakistan":  "",
        "dose_per_acre":        _clean(r.get("spray_dosage", "")),
        "spray_timing":         _clean(r.get("spray_timing", "")),
        "safety_precautions_ur":"",
        "biological_control":   "",
        "economic_loss_pct":    "",

        # Provenance
        "data_source":          _clean(r.get("source", "PARC Plant Diseases Book")),
        "source_page":          r.get("source_page"),
        "verified_year":        2024,
        "country_code":         "PK",
        "confidence":           "Medium",
        "extraction_notes":     "Extracted from scanned PARC book",
        "source_file":          "PARC_Plant_Diseases_Book.pdf",
    }


def _norm_extracted(r: dict) -> dict:
    """
    Normalise an already-rich extracted-schema record.
    These records may already have all fields populated.
    """
    return {
        "id":                   "",
        "crop_name_en":         _clean(r.get("crop_name_en", "")),
        "crop_name_ur":         _clean(r.get("crop_name_ur", "")),
        "disease_name_en":      _clean(r.get("disease_name_en", "")),
        "disease_name_ur":      _clean(r.get("disease_name_ur", "")),

        "pathogen_type":        _clean(r.get("pathogen_type", "")),
        "symptoms_en":          _clean(r.get("symptoms_en", "")),
        "symptoms_ur":          _clean(r.get("symptoms_ur", "")),
        "affected_part":        _clean(r.get("affected_part", "")),
        "disease_stage":        _clean(r.get("disease_stage", "")),

        "season":               _clean(r.get("season", "")),
        "region_pakistan":      _clean(r.get("region_pakistan", "Pakistan")),
        "climate_trigger":      _clean(r.get("climate_trigger", "")),

        "severity_level":       _clean(r.get("severity_level", "")),

        "spray_chemical_en":    _clean(r.get("spray_chemical_en", "")),
        "brand_name_pakistan":  _clean(r.get("brand_name_pakistan", "")),
        "dose_per_acre":        _clean(r.get("dose_per_acre", "")),
        "spray_timing":         _clean(r.get("spray_timing", "")),
        "safety_precautions_ur":_clean(r.get("safety_precautions_ur", "")),
        "biological_control":   _clean(r.get("biological_control", "")),
        "economic_loss_pct":    _clean(r.get("economic_loss_pct", "")),

        "data_source":          _clean(r.get("data_source", "")),
        "source_page":          r.get("source_page"),
        "verified_year":        r.get("verified_year", 2024),
        "country_code":         _clean(r.get("country_code", "PK")),
        "confidence":           _clean(r.get("confidence", "High")),
        "extraction_notes":     _clean(r.get("extraction_notes", "")),
        "source_file":          _clean(r.get("source_file", "")),
    }


def _detect_schema(record: dict) -> str:
    """Detect which schema a JSON record uses."""
    if "crop_name_en" in record:
        return "extracted"
    if "crop_name" in record:
        return "parc"
    return "unknown"


def load_and_normalise(path: Path, verbose: bool) -> list:
    """Load a JSON file and normalise all records to unified schema."""
    if not path.exists():
        if verbose:
            print(f"  {Fore.YELLOW}⚠  Skipping missing file: {path}{Style.RESET_ALL}")
        return []

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        print(f"  {Fore.RED}✗ Not a JSON array: {path}{Style.RESET_ALL}")
        return []

    normed = []
    schema_counts = {}
    for r in raw:
        schema = _detect_schema(r)
        schema_counts[schema] = schema_counts.get(schema, 0) + 1
        if schema == "extracted":
            normed.append(_norm_extracted(r))
        elif schema == "parc":
            normed.append(_norm_parc(r))
        # else: skip unknown schema

    if verbose:
        for s, n in schema_counts.items():
            print(f"    schema={s}: {n} records")

    return normed


def should_keep(rec: dict) -> bool:
    """
    Return True if the record has enough useful information to keep.
    Filter criteria:
      - Must have a non-junk disease_name_en
      - Must have a non-junk crop_name_en
      - Skip pure reference/citation records (no symptoms AND no spray info)
    """
    if _is_junk(rec.get("disease_name_en")):
        return False
    if _is_junk(rec.get("crop_name_en")):
        return False

    # Skip records that look like they're just book citations (reference sections)
    has_symptoms = not _is_junk(rec.get("symptoms_en"))
    has_spray    = not _is_junk(rec.get("spray_chemical_en"))
    has_urdu     = not _is_junk(rec.get("disease_name_ur"))

    # Keep if at least one of these is non-junk
    if has_symptoms or has_spray or has_urdu:
        return True

    # Otherwise discard (likely a bare reference-list entry)
    return False


def dedup_key(rec: dict) -> str:
    """Generate a lowercase deduplication key from crop + disease name."""
    crop    = re.sub(r'\s+', ' ', rec.get("crop_name_en", "").lower().strip())
    disease = re.sub(r'\s+', ' ', rec.get("disease_name_en", "").lower().strip())
    return f"{crop}||{disease}"


def merge(all_records: list, verbose: bool) -> list:
    """
    Deduplicate records. When two records share the same crop+disease key,
    keep the one with more filled fields (richer record).
    """
    seen: dict[str, dict] = {}

    for rec in all_records:
        key = dedup_key(rec)
        if key not in seen:
            seen[key] = rec
        else:
            # Keep whichever record is richer
            existing_richness = _richness(seen[key])
            new_richness      = _richness(rec)
            if new_richness > existing_richness:
                if verbose:
                    print(f"    {Fore.CYAN}↺ Replacing duplicate: {key[:60]}{Style.RESET_ALL}")
                seen[key] = rec

    return list(seen.values())


def assign_ids(records: list) -> list:
    """Assign sequential IDs: PK-001, PK-002 ..."""
    for i, rec in enumerate(records, start=1):
        rec["id"] = f"PK-{i:03d}"
    return records


def main():
    parser = argparse.ArgumentParser(description="Fasal Doctor Data Merger")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed progress")
    parser.add_argument("--out", default="data/processed/master_dataset.json",
                        help="Output path for master dataset")
    args = parser.parse_args()

    verbose = args.verbose
    out_path = Path(args.out)
    processed_dir = Path("data/processed")

    print(f"\n{'='*60}")
    print(f"{Fore.CYAN}FASAL DOCTOR — Data Merger{Style.RESET_ALL}")
    print(f"{'='*60}\n")

    # ── 1. Collect all JSON files to merge ───────────────────────────────
    # Priority files first (extracted is high quality, parc is bulk)
    priority_files = [
        processed_dir / "extracted.json",
        processed_dir / "parc_diseases.json",
    ]

    # Any other JSON in the directory (e.g. scraped.json, extra_records.json)
    extra_files = [
        p for p in sorted(processed_dir.glob("*.json"))
        if p not in priority_files
        and p.name not in ("master_dataset.json",)   # skip output file
    ]

    all_files = priority_files + extra_files

    # ── 2. Load and normalise ─────────────────────────────────────────────
    all_records = []
    for fp in all_files:
        print(f"  📂 Loading: {fp.name}", end=" ")
        recs = load_and_normalise(fp, verbose)
        print(f"→ {Fore.GREEN}{len(recs)} records{Style.RESET_ALL}")
        if verbose:
            pass  # detail printed inside load_and_normalise
        all_records.extend(recs)

    print(f"\n  Total loaded (before filter): {Fore.YELLOW}{len(all_records)}{Style.RESET_ALL}")

    # ── 3. Filter junk records ────────────────────────────────────────────
    before_filter = len(all_records)
    all_records   = [r for r in all_records if should_keep(r)]
    dropped_junk  = before_filter - len(all_records)
    print(f"  Dropped junk/empty records:   {Fore.RED}-{dropped_junk}{Style.RESET_ALL}")
    print(f"  After filter:                 {Fore.GREEN}{len(all_records)}{Style.RESET_ALL}")

    # ── 4. Deduplicate ────────────────────────────────────────────────────
    before_dedup = len(all_records)
    all_records  = merge(all_records, verbose)
    dropped_dup  = before_dedup - len(all_records)
    print(f"  Dropped duplicate records:    {Fore.RED}-{dropped_dup}{Style.RESET_ALL}")
    print(f"  After dedup:                  {Fore.GREEN}{len(all_records)}{Style.RESET_ALL}")

    # ── 5. Assign final IDs ───────────────────────────────────────────────
    all_records = assign_ids(all_records)

    # ── 6. Summary by crop ────────────────────────────────────────────────
    crop_counts: dict[str, int] = {}
    for rec in all_records:
        crop = rec.get("crop_name_en", "Unknown")
        crop_counts[crop] = crop_counts.get(crop, 0) + 1

    print(f"\n  {Fore.CYAN}Crops in master dataset:{Style.RESET_ALL}")
    for crop, n in sorted(crop_counts.items(), key=lambda x: -x[1])[:20]:
        bar = "█" * min(n, 30)
        print(f"    {crop:<25} {bar} {n}")
    if len(crop_counts) > 20:
        print(f"    ... and {len(crop_counts) - 20} more crops")

    # ── 7. Save ──────────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"\n  {Fore.GREEN}✓ Master dataset saved → {out_path}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}✓ Total records: {len(all_records)}{Style.RESET_ALL}")
    print(f"\n  Next steps:")
    print(f"    python src/urdu_enricher.py --input {out_path}")
    print(f"    python src/reviewer.py --input {out_path} --export")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
