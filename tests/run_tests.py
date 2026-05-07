import json
import sys
import re
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag_engine import get_diagnosis, _API_KEYS

def run_tests():
    with open("tests/test_queries.json", "r", encoding="utf-8") as f:
        queries = json.load(f)

    results = []
    passed = 0
    total = len(queries)

    print(f"Running {total} tests...")
    print(f"API keys loaded: {len(_API_KEYS)} (rate limit shared across all keys)\n")

    # Adaptive inter-request delay.
    # With N unique keys each at 15 RPM, we can safely fire 1 req/s up to N keys.
    # Start at 1s; on a rate-limit event the RAG engine rotates keys internally.
    BASE_DELAY = 1.0

    for i, q_dict in enumerate(queries):
        query = q_dict["query"]
        print(f"Test {i+1}/{total}: {query}")
        
        try:
            response = get_diagnosis(query, top_k=3)
        except Exception as e:
            response = f"Error: {e}"

        time.sleep(BASE_DELAY)  # polite inter-request gap

        is_edge_case = (i >= 40)
        
        disease_match = re.search(r"\*\*Disease Name \(English\):\*\*\s*(.+)", response, re.IGNORECASE)
        if disease_match:
            disease_name = disease_match.group(1).strip().lower()
            invalid_names = ["unsure", "cannot diagnose", "unable to diagnose", "unknown", "unspecified", "not enough information"]
            has_disease = not any(x in disease_name for x in invalid_names)
        else:
            has_disease = False
            
        has_spray = bool(re.search(r"Spray Chemical|Spray|Treatment|علاج|دوائی", response, re.IGNORECASE))
        has_urdu = bool(re.search(r"[\u0600-\u06FF]", response))
        
        has_fallback = "UNKNOWN_CROP_FLAG" in response or "LOW_CONFIDENCE_FLAG" in response or "API_ERROR_FLAG" in response
        
        if is_edge_case:
            # Edge case passes if it triggers a fallback or DOES NOT confidently predict a disease
            test_passed = has_fallback or (not has_disease)
        else:
            # Normal case passes if it gives a disease, spray, and Urdu
            test_passed = has_disease and has_spray and has_urdu

        if test_passed:
            passed += 1
            print(f"  [✓] PASSED")
        else:
            # Print specific reason so failures are easy to debug
            reasons = []
            if not has_disease: reasons.append("no disease name")
            if not has_spray:   reasons.append("no spray info")
            if not has_urdu:    reasons.append("no Urdu text")
            if is_edge_case and not has_fallback and has_disease:
                reasons.append("should have triggered fallback")
            print(f"  [✗] FAILED ({', '.join(reasons) if reasons else 'edge-case logic'})")

        results.append({
            "query": query,
            "response": response[:200] + "..." if len(response) > 200 else response,
            "passed": test_passed,
            "is_edge_case": is_edge_case,
            "metrics": {
                "has_disease": has_disease,
                "has_spray": has_spray,
                "has_urdu": has_urdu,
                "has_fallback": has_fallback
            }
        })

    print(f"\nFinal Score: {passed}/{total} passed ({(passed/total)*100:.1f}%)")

    with open("tests/test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Results saved to tests/test_results.json")

if __name__ == "__main__":
    run_tests()
