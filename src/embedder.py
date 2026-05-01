"""
FASAL DOCTOR — Embedder (STEP 6)
==================================
Reads master_dataset.json and builds a ChromaDB vector store.
Run this ONCE to create the vector database; rag_engine.py reuses it.

Embedding model: paraphrase-multilingual-MiniLM-L12-v2
  — chosen because it handles Urdu + English in the same vector space.
  — small (470MB), runs on CPU, no GPU needed.

ChromaDB is stored locally in: data/chroma_db/

Usage:
    pip install chromadb sentence-transformers
    python src/embedder.py
    python src/embedder.py --input data/processed/master_dataset.json
    python src/embedder.py --reset   # wipe and rebuild from scratch
"""

import os, sys, json, argparse
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

CHROMA_DIR    = "data/chroma_db"
COLLECTION    = "fasal_doctor_diseases"
EMBED_MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_INPUT = "data/processed/master_dataset.json"


def build_document(rec: dict) -> str:
    """
    Build a rich text string from a disease record for embedding.
    Combines English and Urdu text so queries in either language match.
    """
    parts = []

    # Crop and disease (EN + UR)
    crop = rec.get("crop_name_en", "")
    crop_ur = rec.get("crop_name_ur", "")
    disease = rec.get("disease_name_en", "")
    disease_ur = rec.get("disease_name_ur", "")

    if crop:    parts.append(f"Crop: {crop}")
    if crop_ur: parts.append(f"فصل: {crop_ur}")
    if disease: parts.append(f"Disease: {disease}")
    if disease_ur: parts.append(f"بیماری: {disease_ur}")

    # Symptoms (EN + UR) — most important for matching queries
    symp_en = rec.get("symptoms_en", "")
    symp_ur = rec.get("symptoms_ur", "")
    if symp_en and symp_en.lower() not in ("not specified","not mentioned","n/a","consult agronomist",""):
        parts.append(f"Symptoms: {symp_en}")
    if symp_ur:
        parts.append(f"علامات: {symp_ur}")

    # Treatment
    spray = rec.get("spray_chemical_en", "")
    brand = rec.get("brand_name_pakistan", "")
    dose  = rec.get("dose_per_acre", "")
    if spray and spray.lower() not in ("consult agronomist", ""):
        parts.append(f"Treatment: {spray}")
    if brand:
        parts.append(f"Brand: {brand}")
    if dose and dose.lower() not in ("consult agronomist", ""):
        parts.append(f"Dose: {dose}")

    # Extra context
    for field in ("affected_part", "season", "region_pakistan", "severity_level",
                  "pathogen_type", "biological_control"):
        val = rec.get(field, "")
        if val and val.lower() not in ("", "unknown", "not specified"):
            parts.append(f"{field.replace('_',' ').title()}: {val}")

    return " | ".join(parts)


def build_metadata(rec: dict) -> dict:
    """
    Build the ChromaDB metadata dict from a record.
    Only scalar values allowed (no None — replace with "").
    """
    def safe(v):
        if v is None: return ""
        return str(v)

    return {
        "id":                  safe(rec.get("id")),
        "crop_name_en":        safe(rec.get("crop_name_en")),
        "crop_name_ur":        safe(rec.get("crop_name_ur")),
        "disease_name_en":     safe(rec.get("disease_name_en")),
        "disease_name_ur":     safe(rec.get("disease_name_ur")),
        "pathogen_type":       safe(rec.get("pathogen_type")),
        "symptoms_en":         safe(rec.get("symptoms_en")),
        "symptoms_ur":         safe(rec.get("symptoms_ur")),
        "affected_part":       safe(rec.get("affected_part")),
        "season":              safe(rec.get("season")),
        "region_pakistan":     safe(rec.get("region_pakistan")),
        "severity_level":      safe(rec.get("severity_level")),
        "spray_chemical_en":   safe(rec.get("spray_chemical_en")),
        "brand_name_pakistan": safe(rec.get("brand_name_pakistan")),
        "dose_per_acre":       safe(rec.get("dose_per_acre")),
        "spray_timing":        safe(rec.get("spray_timing")),
        "safety_precautions_ur": safe(rec.get("safety_precautions_ur")),
        "biological_control":  safe(rec.get("biological_control")),
        "economic_loss_pct":   safe(rec.get("economic_loss_pct")),
        "data_source":         safe(rec.get("data_source")),
        "confidence":          safe(rec.get("confidence")),
        "source_page":         safe(rec.get("source_page")),
    }


def main():
    parser = argparse.ArgumentParser(description="Fasal Doctor Embedder")
    parser.add_argument("--input",  default=DEFAULT_INPUT)
    parser.add_argument("--reset",  action="store_true",
                        help="Delete existing ChromaDB and rebuild from scratch")
    parser.add_argument("--batch",  type=int, default=50,
                        help="Embedding batch size (default: 50)")
    args = parser.parse_args()

    # ── Imports (done here so missing packages give a clean error) ─────────
    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"\n{Fore.RED}Missing package: {e}{Style.RESET_ALL}")
        print("Run: pip install chromadb sentence-transformers")
        sys.exit(1)

    # ── Load records ───────────────────────────────────────────────────────
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"{Fore.RED}Input file not found: {input_path}{Style.RESET_ALL}")
        print("Run: python src/data_merger.py   first")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        records = json.load(f)

    print(f"\n{'='*60}")
    print(f"{Fore.CYAN}FASAL DOCTOR — Building Vector Store{Style.RESET_ALL}")
    print(f"{'='*60}")
    print(f"  Input:       {input_path}  ({len(records)} records)")
    print(f"  Embed model: {EMBED_MODEL}")
    print(f"  ChromaDB:    {CHROMA_DIR}")

    # ── Init ChromaDB ──────────────────────────────────────────────────────
    chroma_path = Path(CHROMA_DIR)
    chroma_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_path))

    if args.reset:
        try:
            client.delete_collection(COLLECTION)
            print(f"\n  {Fore.YELLOW}Deleted existing collection: {COLLECTION}{Style.RESET_ALL}")
        except Exception:
            pass

    # ── Load embedding model ───────────────────────────────────────────────
    print(f"\n  Loading embedding model (first run downloads ~470MB)...")
    embedder = SentenceTransformer(EMBED_MODEL)
    print(f"  {Fore.GREEN}✓ Model loaded{Style.RESET_ALL}")

    # ── Get or create collection ───────────────────────────────────────────
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    existing_ids = set(collection.get()["ids"])
    print(f"  Existing vectors in DB: {len(existing_ids)}")

    # ── Embed and upsert in batches ────────────────────────────────────────
    new_count = 0
    batch_docs, batch_ids, batch_metas = [], [], []

    for rec in records:
        rec_id = rec.get("id", "")
        if not rec_id:
            continue
        if rec_id in existing_ids:
            continue  # already embedded, skip

        doc  = build_document(rec)
        meta = build_metadata(rec)

        batch_docs.append(doc)
        batch_ids.append(rec_id)
        batch_metas.append(meta)

        if len(batch_docs) >= args.batch:
            embeddings = embedder.encode(batch_docs, show_progress_bar=False).tolist()
            collection.add(
                documents=batch_docs,
                embeddings=embeddings,
                ids=batch_ids,
                metadatas=batch_metas,
            )
            new_count += len(batch_docs)
            print(f"  {Fore.GREEN}✓ Embedded {new_count} / {len(records)} records...{Style.RESET_ALL}",
                  end="\r")
            batch_docs, batch_ids, batch_metas = [], [], []

    # Flush remaining
    if batch_docs:
        embeddings = embedder.encode(batch_docs, show_progress_bar=False).tolist()
        collection.add(
            documents=batch_docs,
            embeddings=embeddings,
            ids=batch_ids,
            metadatas=batch_metas,
        )
        new_count += len(batch_docs)

    total = collection.count()
    print(f"\n  {Fore.GREEN}✓ Added {new_count} new vectors{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}✓ Total vectors in DB: {total}{Style.RESET_ALL}")
    print(f"\n  Run the RAG engine:")
    print(f"    python src/rag_engine.py")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
