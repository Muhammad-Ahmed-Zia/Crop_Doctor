"""
src/class_to_query.py
═══════════════════════════════════════════════════════════════
FASAL DOCTOR — Phase 2
CNN Class → RAG Query Mapping

After a CNN model predicts a disease class name, this module
provides the correct text query to pass to get_diagnosis().

Usage:
    from src.class_to_query import CLASS_TO_QUERY, get_rag_query

    query = get_rag_query("wheat", "yellow_rust")
    # → "Yellow Rust disease wheat"
    # Returns None for "healthy" (no RAG lookup needed)
═══════════════════════════════════════════════════════════════
"""

# ── Mapping: crop → {class_name → RAG query string} ──────────
# Value is None for "healthy" — no disease lookup needed.
# Class names must match exact folder names in data/images/.
CLASS_TO_QUERY: dict[str, dict[str, str | None]] = {

    "wheat": {
        "yellow_rust":      "Yellow Rust disease wheat",
        "brown_rust":       "Brown Rust Leaf Rust wheat",
        "leaf_blight":      "Leaf Blight wheat",
        "powdery_mildew":   "Powdery Mildew wheat",
        "aphid":            "Wheat aphid pest damage",
        "mite":             "Wheat mite pest damage",
        "stem_fly":         "Wheat stem fly pest",
        "healthy":          None,
    },

    # NOTE: The cotton dataset on disk (data/raw/Cotton) is the
    # saeedazfar customised dataset. Actual classes found are:
    #   aphids, army_worm, bacterial_blight, boll_rot,
    #   green_boll, powdery_mildew, target_spot, healthy
    # These queries are set accordingly.
    # If you later swap in the grey_mildew/fusarium_wilt dataset,
    # update both organize_images.py and the entries below.
    "cotton": {
        "aphids":              "Aphids infestation cotton",
        "army_worm":           "Army Worm damage cotton",
        "bacterial_blight":    "Bacterial Blight cotton",
        "boll_rot":            "Cotton Boll Rot disease",
        "green_boll":          "Green Cotton Boll disorder",
        "powdery_mildew":      "Powdery Mildew cotton",
        "target_spot":         "Target Spot cotton Corynespora",
        "healthy":             None,
        # Legacy keys (if correct dataset added later)
        "grey_mildew":         "Grey Mildew cotton",
        "fusarium_wilt":       "Fusarium Wilt cotton",
        "cercospora":          "Cercospora Leaf Spot cotton",
        "curl_virus":          "Cotton Leaf Curl Virus CLCuV",
        "alternaria":          "Alternaria Leaf Spot cotton",
    },

    "rice": {
        "bacterial_blight":  "Bacterial Blight rice Xanthomonas",
        "brown_spot":        "Brown Spot rice Helminthosporium",
        "leaf_smut":         "Leaf Smut rice Entyloma",
        "healthy":           None,
    },

    "sugarcane": {
        "mosaic":   "Mosaic disease sugarcane",
        "red_rot":  "Red Rot sugarcane Colletotrichum",
        "rust":     "Rust disease sugarcane Puccinia",
        "yellow":   "Yellow disease sugarcane Phytoplasma",
        "healthy":  None,
    },

    "maize": {
        "common_rust":     "Common Rust maize Puccinia sorghi",
        "gray_leaf_spot":  "Gray Leaf Spot maize Cercospora",
        "northern_blight": "Northern Leaf Blight maize Exserohilum",
        "healthy":         None,
    },

    "potato": {
        "late_blight":  "Late Blight potato Phytophthora infestans",
        "early_blight": "Early Blight potato Alternaria solani",
        "healthy":      None,
    },

    "tomato": {
        "early_blight":           "Early Blight tomato Alternaria",
        "late_blight":            "Late Blight tomato Phytophthora",
        "leaf_curl":              "Leaf Curl tomato virus",
        "bacterial_spot":         "Bacterial Spot tomato Xanthomonas",
        "spotted_wilt_virus":     "Spotted Wilt Virus tomato TSWV",
        "leaf_miner":             "Leaf Miner tomato pest",
        "magnesium_deficiency":   "Magnesium deficiency tomato nutrient",
        "nitrogen_deficiency":    "Nitrogen deficiency tomato nutrient",
        "potassium_deficiency":   "Potassium deficiency tomato nutrient",
        "healthy":                None,
    },
}


# ── Helper function ───────────────────────────────────────────
def get_rag_query(crop: str, class_name: str) -> str | None:
    """
    Return the RAG query string for a given (crop, class_name) pair.

    Args:
        crop:       e.g. "wheat", "cotton", "rice"
        class_name: e.g. "yellow_rust", "healthy"

    Returns:
        str   — RAG query to pass to get_diagnosis()
        None  — class is healthy, no RAG lookup needed
        str   — "<crop> <class_name> disease" as fallback if not found
    """
    crop_map = CLASS_TO_QUERY.get(crop.lower(), {})
    if class_name in crop_map:
        return crop_map[class_name]

    # Case-insensitive fallback
    for k, v in crop_map.items():
        if k.lower() == class_name.lower():
            return v

    # If not mapped and not healthy → generic fallback
    if "healthy" in class_name.lower():
        return None

    return f"{class_name.replace('_', ' ')} disease {crop}"


# ── Quick self-test ───────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== CLASS_TO_QUERY Self-Test ===\n")
    tests = [
        ("wheat",     "yellow_rust"),
        ("wheat",     "healthy"),
        ("cotton",    "bacterial_blight"),
        ("rice",      "brown_spot"),
        ("sugarcane", "red_rot"),
        ("maize",     "northern_blight"),
        ("potato",    "late_blight"),
        ("tomato",    "early_blight"),
        ("tomato",    "spotted_wilt_virus"),
        ("wheat",     "unknown_class"),
    ]
    for crop, cls in tests:
        q = get_rag_query(crop, cls)
        print(f"  {crop:<12} {cls:<25} → {repr(q)}")
    print()
    print(f"Total crops configured: {len(CLASS_TO_QUERY)}")
    total = sum(len(v) for v in CLASS_TO_QUERY.values())
    print(f"Total class mappings  : {total}")
