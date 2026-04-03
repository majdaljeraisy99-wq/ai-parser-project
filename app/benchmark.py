import json
import time
import psutil

from parser import parse_document
from chunking import chunk_document
from storage import StorageManager
from retrieval import Retriever
from utils import contains_diacritics


def run_document_benchmark(file_path: str):
    storage = StorageManager()
    storage.clear_document_data()

    mem_before = psutil.Process().memory_info().rss / (1024 * 1024)

    t0 = time.time()
    parsed = parse_document(file_path)
    parse_time = time.time() - t0

    t1 = time.time()
    strategy, chunks = chunk_document(parsed["text"])
    chunk_time = time.time() - t1

    t2 = time.time()
    document_id = storage.save_document(
        parsed["metadata"],
        strategy,
        len(chunks),
        parsed["text"]
    )
    storage.save_chunks(document_id, chunks, parsed["metadata"]["language"])
    store_time = time.time() - t2

    mem_after = psutil.Process().memory_info().rss / (1024 * 1024)

    return {
        "file_name": parsed["metadata"]["file_name"],
        "language": parsed["metadata"]["language"],
        "strategy": strategy,
        "num_chunks": len(chunks),
        "parse_time_sec": round(parse_time, 4),
        "chunk_time_sec": round(chunk_time, 4),
        "store_time_sec": round(store_time, 4),
        "memory_used_mb": round(mem_after - mem_before, 2),
        "has_diacritics": contains_diacritics(parsed["text"])
    }


def run_retrieval_benchmark(test_cases_path: str):
    storage = StorageManager()
    retriever = Retriever(storage)

    with open(test_cases_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases)
    hits = 0
    details = []

    for case in test_cases:
        query = case["query"]
        expected_keywords = case["expected_keywords"]

        results = retriever.hybrid_search(query, top_k=3)
        combined_text = " ".join([r["full_chunk"] for r in results]).lower()

        passed = any(keyword.lower() in combined_text for keyword in expected_keywords)
        if passed:
            hits += 1

        details.append({
            "query": query,
            "passed": passed,
            "results_found": len(results)
        })

    accuracy = hits / total if total else 0.0

    return {
        "retrieval_accuracy": round(accuracy, 4),
        "total_cases": total,
        "passed_cases": hits,
        "details": details
    }


if __name__ == "__main__":
    doc_metrics = run_document_benchmark("../data/sample.txt")
    retrieval_metrics = run_retrieval_benchmark("../data/test_cases.json")

    print("Document Benchmark")
    print(doc_metrics)
    print("\nRetrieval Benchmark")
    print(retrieval_metrics)