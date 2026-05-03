"""
FASAL DOCTOR — RAG Engine (STEP 5)
=====================================
Core query engine: retrieves disease records from ChromaDB
and passes them to Gemini 2.0 Flash for bilingual response.

Usage:
    python src/rag_engine.py
    python src/rag_engine.py --query "میری گندم کے پتوں پر پیلے دھبے ہیں"
    python src/rag_engine.py --crop wheat
    python src/rag_engine.py --top-k 5
"""

import os, sys, json, argparse, re, time
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init

from google import genai

init(autoreset=True)
load_dotenv()

# ── API Key Rotation ──────────────────────────────────────────────────────────
_API_KEYS = [
    os.getenv("GEMINI_RAG_KEY_3"),
    os.getenv("GEMINI_RAG_KEY_7"), 
    os.getenv("GEMINI_RAG_KEY_5"),
    os.getenv("GEMINI_RAG_KEY_6"), 
      # dedicated RAG key (highest priority)
]
_API_KEYS = [k for k in _API_KEYS if k]   # drop unset keys
_current_key_idx = 0
_gemini_client = None


def _get_client() -> genai.Client:
    """Return the active Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        if not _API_KEYS:
            print(f"{Fore.RED}No Gemini API keys found. Add GEMINI_API_KEY to .env{Style.RESET_ALL}")
            sys.exit(1)
        _gemini_client = genai.Client(api_key=_API_KEYS[_current_key_idx])
    return _gemini_client


def _rotate_key() -> bool:
    """Switch to the next available API key. Returns False if all exhausted."""
    global _current_key_idx, _gemini_client
    _current_key_idx += 1
    if _current_key_idx >= len(_API_KEYS):
        return False
    _gemini_client = genai.Client(api_key=_API_KEYS[_current_key_idx])
    print(f"{Fore.YELLOW}  🔄 Switched to API key #{_current_key_idx + 1}{Style.RESET_ALL}")
    return True

# ── Config ────────────────────────────────────────────────────────────────
CHROMA_DIR  = "data/chroma_db"
COLLECTION  = "fasal_doctor_diseases"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
GEMINI_MODEL= "gemini-2.5-flash-lite"
TOP_K       = 3        # number of records to retrieve

# ── System prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are FASAL DOCTOR (فصل ڈاکٹر), an AI agricultural advisor for Pakistani farmers.
You speak both Urdu and English. Always respond in BOTH languages.

Your job:
- Diagnose the crop disease based on symptoms described
- Recommend the correct spray with Pakistan-available brand name
- Give dose per acre clearly
- Warn about safety in Urdu (simple language, uneducated farmers can understand)
- State severity level and economic loss risk

Rules:
- Never recommend a pesticide not available in Pakistan
- Always mention the Urdu name of the disease
- Keep Urdu simple — no complex vocabulary
- If you are unsure, say so clearly in both languages
- Format your response cleanly with clear sections
"""

RAG_PROMPT_TEMPLATE = """
A Pakistani farmer has described this problem:
"{query}"

Based on the disease database, here are the most relevant records:

{context}

Using ONLY the information above (plus general agricultural knowledge for Pakistan),
provide a complete diagnosis and treatment plan.

Respond in this exact format:

---
🌾 DISEASE DIAGNOSIS | بیماری کی تشخیص
---

**Disease Name (English):** [name]
**بیماری کا نام (اردو):** [name]
**Affected Crop:** [crop]
**متاثرہ فصل:** [crop in Urdu]

---
🔍 SYMPTOMS | علامات
---

**English:** [symptoms]
**اردو:** [symptoms in simple Urdu]

---
💊 TREATMENT | علاج
---

**Spray Chemical:** [chemical name]
**Pakistan Brand:** [brand name — must be available in Pakistan]
**Dose per Acre:** [dose]
**Spray Timing:** [when to spray]

---
⚠️ SAFETY WARNING | حفاظتی ہدایات
---

[Safety warning in simple Urdu that an uneducated farmer can understand]

---
📊 SEVERITY & LOSSES | نقصانات
---

**Severity:** [level]
**Potential Yield Loss:** [percentage]

---
🌿 BIOLOGICAL CONTROL | قدرتی طریقہ
---

[Resistant varieties or biological control methods if available]
"""


# ── ChromaDB + Embedder loader ─────────────────────────────────────────────

def load_retriever():
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"{Fore.RED}Missing: {e}{Style.RESET_ALL}")
        print("Run: pip install chromadb sentence-transformers")
        sys.exit(1)

    chroma_path = Path(CHROMA_DIR)
    if not chroma_path.exists():
        print(f"{Fore.RED}ChromaDB not found at {CHROMA_DIR}{Style.RESET_ALL}")
        print("Run: python src/embedder.py   first")
        sys.exit(1)

    client     = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(COLLECTION)
    embedder   = SentenceTransformer(EMBED_MODEL)

    total = collection.count()
    print(f"  {Fore.GREEN}✓ ChromaDB loaded — {total} disease vectors{Style.RESET_ALL}")

    return collection, embedder


def retrieve(query: str, collection, embedder, top_k: int = TOP_K,
             crop_filter: str = "") -> list[dict]:
    """
    Embed the query and retrieve top-k similar disease records.
    Optional crop_filter narrows results to a specific crop.
    """
    query_vec = embedder.encode([query])[0].tolist()

    where = None
    if crop_filter:
        # ChromaDB where filter — case-insensitive match via $contains isn't
        # supported, so we pass the crop name as-is (user provides it)
        where = {"crop_name_en": {"$eq": crop_filter.capitalize()}}

    try:
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # If where filter fails (empty results), retry without it
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    records = []
    for i, meta in enumerate(results["metadatas"][0]):
        rec = dict(meta)
        rec["_distance"] = results["distances"][0][i]
        rec["_document"] = results["documents"][0][i]
        records.append(rec)

    return records


def build_context(records: list[dict]) -> str:
    """Format retrieved records into a readable context block for Gemini."""
    parts = []
    for i, rec in enumerate(records, 1):
        confidence = 1 - rec.get("_distance", 0.5)
        block = [
            f"[RECORD {i}] (Relevance: {confidence:.0%})",
            f"  Crop: {rec.get('crop_name_en','')} ({rec.get('crop_name_ur','')})",
            f"  Disease: {rec.get('disease_name_en','')} — {rec.get('disease_name_ur','')}",
            f"  Symptoms: {rec.get('symptoms_en','')}",
        ]
        if rec.get("symptoms_ur"):
            block.append(f"  علامات: {rec.get('symptoms_ur')}")
        if rec.get("spray_chemical_en") and rec.get("spray_chemical_en") != "Consult agronomist":
            block.append(f"  Spray: {rec.get('spray_chemical_en')}")
        if rec.get("brand_name_pakistan"):
            block.append(f"  Pakistan Brand: {rec.get('brand_name_pakistan')}")
        if rec.get("dose_per_acre"):
            block.append(f"  Dose: {rec.get('dose_per_acre')}")
        if rec.get("spray_timing"):
            block.append(f"  Timing: {rec.get('spray_timing')}")
        if rec.get("severity_level"):
            block.append(f"  Severity: {rec.get('severity_level')}")
        if rec.get("safety_precautions_ur"):
            block.append(f"  Safety (Urdu): {rec.get('safety_precautions_ur')}")
        if rec.get("biological_control"):
            block.append(f"  Biological Control: {rec.get('biological_control')}")
        if rec.get("economic_loss_pct"):
            block.append(f"  Economic Loss: {rec.get('economic_loss_pct')}")
        parts.append("\n".join(block))

    return "\n\n".join(parts)


def ask_gemini(query: str, context: str, _unused_client=None) -> str:
    """Send the query + retrieved context to Gemini. Auto-retries on rate limits."""
    full_prompt = SYSTEM_PROMPT + "\n\n" + RAG_PROMPT_TEMPLATE.format(
        query=query, context=context
    )

    while True:
        try:
            response = _get_client().models.generate_content(
                model=GEMINI_MODEL,
                contents=full_prompt,
            )
            return response.text

        except Exception as e:
            err = str(e)

            # httpx client closed (happens in Streamlit reruns) — recreate and retry
            if "client has been closed" in err.lower() or "cannot send a request" in err.lower():
                global _gemini_client
                _gemini_client = None   # force fresh client on next _get_client() call
                print(f"{Fore.YELLOW}  🔄 Gemini client was closed — recreating...{Style.RESET_ALL}")
                continue

            # Per-minute rate limit — wait, then retry same key
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                delay = 30
                match = re.search(r"retryDelay.*?(\d+)s", err)
                if match:
                    delay = int(match.group(1)) + 3
                print(f"{Fore.YELLOW}  ⏳ Rate limited — waiting {delay}s then retrying...{Style.RESET_ALL}")
                time.sleep(delay)
                continue   # retry same key after wait

            # Daily quota exhausted — rotate key
            if "limit: 0" in err or "GenerateRequestsPerDay" in err or "403" in err:
                print(f"{Fore.YELLOW}  🔑 Key #{_current_key_idx + 1} exhausted, rotating...{Style.RESET_ALL}")
                if _rotate_key():
                    continue   # retry with new key
                return "All API keys exhausted. Try again tomorrow."

            # Unexpected error — return message
            return f"[Gemini error: {err[:300]}]"


def print_response(response: str):
    """Pretty-print the Gemini response."""
    print(f"\n{'='*60}")
    print(f"{Fore.GREEN}{response}{Style.RESET_ALL}")
    print(f"{'='*60}\n")


def interactive_cli(collection, embedder, gemini_client):
    """Run an interactive CLI chatbot loop."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("  فصل ڈاکٹر — FASAL DOCTOR  |  Crop Disease Advisor")
    print(f"{'='*60}{Style.RESET_ALL}")
    print("  Type your question in Urdu or English.")
    print("  Type 'quit' or 'q' to exit.\n")

    while True:
        try:
            query = input(f"{Fore.YELLOW}Your question: {Style.RESET_ALL}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye | خدا حافظ")
            break

        if not query:
            continue
        if query.lower() in ("quit", "q", "exit", "bye"):
            print("Goodbye | خدا حافظ")
            break

        print(f"\n{Fore.CYAN}🔍 Searching disease database...{Style.RESET_ALL}")
        records = retrieve(query, collection, embedder)

        if not records:
            print(f"{Fore.RED}No matching diseases found.{Style.RESET_ALL}")
            continue

        print(f"  Found {len(records)} relevant records")
        print(f"{Fore.CYAN}🤖 Generating diagnosis with Gemini...{Style.RESET_ALL}")

        context  = build_context(records)
        response = ask_gemini(query, context, gemini_client)
        print_response(response)


def main():
    parser = argparse.ArgumentParser(description="Fasal Doctor RAG Engine")
    parser.add_argument("--query",  "-q", help="Single query (non-interactive mode)")
    parser.add_argument("--crop",   "-c", help="Filter results by crop name")
    parser.add_argument("--top-k",  "-k", type=int, default=TOP_K,
                        help=f"Number of records to retrieve (default: {TOP_K})")
    args = parser.parse_args()

    # ── API Key (rotation handled globally) ───────────────────────────────
    if not _API_KEYS:
        print(f"{Fore.RED}Set GEMINI_API_KEY in .env file{Style.RESET_ALL}")
        sys.exit(1)
    gemini_client = _get_client()   # initialise first key

    # ── Load retriever ─────────────────────────────────────────────────────
    print(f"\n{Fore.CYAN}Loading Fasal Doctor RAG Engine...{Style.RESET_ALL}")
    collection, embedder = load_retriever()

    # ── Single query mode ──────────────────────────────────────────────────
    if args.query:
        print(f"\n{Fore.CYAN}Query: {args.query}{Style.RESET_ALL}")
        records = retrieve(args.query, collection, embedder,
                           top_k=args.top_k, crop_filter=args.crop or "")
        if not records:
            print(f"{Fore.RED}No matching diseases found.{Style.RESET_ALL}")
            sys.exit(0)
        context  = build_context(records)
        response = ask_gemini(args.query, context, gemini_client)
        print_response(response)
        return

    # ── Interactive mode ───────────────────────────────────────────────────
    interactive_cli(collection, embedder, gemini_client)


# ── Public API (used by Streamlit and any other importer) ─────────────────────
_retriever_cache: dict = {}


def get_retriever():
    """Load and cache the ChromaDB collection + sentence embedder (heavy — once only)."""
    if not _retriever_cache:
        collection, embedder = load_retriever()
        _retriever_cache["collection"] = collection
        _retriever_cache["embedder"]   = embedder
    return _retriever_cache["collection"], _retriever_cache["embedder"]


def get_diagnosis(query: str,
                  crop_filter: str | None = None,
                  language: str = "both",
                  top_k: int = TOP_K) -> str:
    """
    Public callable for Streamlit / external importers.

    Args:
        query       : Farmer's question in Urdu or English.
        crop_filter : Optional crop name to narrow retrieval (e.g. "Wheat").
        language    : "english" | "urdu" | "both"  (hint passed to Gemini).
        top_k       : Number of disease records to retrieve from ChromaDB.

    Returns:
        Full diagnosis text from Gemini (markdown-formatted).
    """
    collection, embedder = get_retriever()
    records = retrieve(query, collection, embedder,
                       top_k=top_k, crop_filter=crop_filter or "")
    if not records:
        return (
            "No matching diseases found in the database for your query.\n\n"
            "آپ کے سوال سے ملتی جلتی کوئی بیماری ڈیٹا بیس میں نہیں ملی۔ "
            "براہ کرم علامات کو مختلف الفاظ میں بیان کریں۔"
        )
    context = build_context(records)
    return ask_gemini(query, context)


if __name__ == "__main__":
    main()
