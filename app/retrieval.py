import re
from utils import normalize_text, safe_preview


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def split_sentences(text: str) -> list[str]:
    text = text.replace("\n", " ")
    parts = re.split(r'(?<=[\.\!\؟\?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def extract_speaker_from_query(query: str) -> str | None:
    q = normalize_text(query)

    patterns = [
        r"ماذا قال (\w+)",
        r"وش قال (\w+)",
        r"ما قال (\w+)",
        r"what did (\w+) say",
        r"what did (\w+) say\?"
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return match.group(1)

    return None


def extract_quote_after_speech(sentence: str, speaker: str) -> str | None:
    s = sentence.strip()
    speaker_norm = normalize_text(speaker)

    if ":" in s:
        before, after = s.split(":", 1)
        before_norm = normalize_text(before)

        if speaker_norm in before_norm and ("قال" in before_norm or "said" in before_norm):
            after = after.strip().strip(' "\'«»“”')
            if len(after.split()) >= 2:
                return after

    quote_match = re.search(r'["«“](.*?)["»”]', s)
    if quote_match:
        result = quote_match.group(1).strip()
        if len(result.split()) >= 2:
            return result

    return None


def sentence_keyword_score(sentence: str, query: str) -> float:
    sentence_norm = normalize_text(sentence)
    query_norm = normalize_text(query)

    query_words = [w for w in query_norm.split() if len(w) >= 2]
    if not query_words:
        return 0.0

    score = 0.0
    matched_words = 0

    for word in query_words:
        if word in sentence_norm:
            score += 2.0
            matched_words += 1

    if query_norm in sentence_norm:
        score += 5.0

    if "قال" in query_norm and "قال" in sentence_norm:
        score += 2.0
    if "say" in query_norm and "said" in sentence_norm:
        score += 2.0

    score = score / (len(sentence_norm.split()) + 1)

    if matched_words == 0:
        return 0.0

    return round(score, 4)


class Retriever:
    def __init__(self, storage):
        self.storage = storage
        self.model = None

    def get_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(MODEL_NAME)
        return self.model

    def semantic_search(self, query: str, top_k: int = 3) -> list[dict]:
        try:
            collection = self.storage.get_collection()
            model = self.get_model()

            query_embedding = model.encode([query]).tolist()[0]

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            docs = results.get("documents", [[]])[0] if results else []
            metas = results.get("metadatas", [[]])[0] if results else []

            final_results = []
            for i, doc in enumerate(docs):
                metadata = metas[i] if i < len(metas) else {}
                final_results.append({
                    "answer": safe_preview(doc),
                    "full_chunk": doc,
                    "metadata": metadata,
                    "method": "semantic"
                })

            return final_results

        except Exception:
            return []

    def keyword_search(self, query: str, top_k: int = 3) -> list[dict]:
        chunks = self.storage.get_all_chunks()
        scored = []

        for chunk in chunks:
            chunk_score = sentence_keyword_score(chunk, query)
            if chunk_score > 0:
                scored.append((chunk_score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "answer": safe_preview(chunk),
                "full_chunk": chunk,
                "metadata": {"score": score},
                "method": "keyword"
            })

        return results

    def extract_best_sentence(self, chunk: str, query: str) -> str:
        sentences = split_sentences(chunk)
        if not sentences:
            return safe_preview(chunk)

        speaker = extract_speaker_from_query(query)

        if speaker:
            for sentence in sentences:
                extracted = extract_quote_after_speech(sentence, speaker)
                if extracted:
                    return extracted

        best_sentence = None
        best_score = 0.0

        for sentence in sentences:
            score = sentence_keyword_score(sentence, query)
            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_sentence:
            return best_sentence

        return safe_preview(chunk)

    def improve_results(self, results: list[dict], query: str) -> list[dict]:
        improved = []

        for item in results:
            full_chunk = item["full_chunk"]
            best_answer = self.extract_best_sentence(full_chunk, query)

            improved.append({
                "answer": best_answer,
                "full_chunk": full_chunk,
                "metadata": item.get("metadata", {}),
                "method": item.get("method", "unknown")
            })

        return improved

    def deduplicate_results(self, results: list[dict]) -> list[dict]:
        unique = []
        seen = set()

        for item in results:
            key = item["answer"].strip()
            if key and key not in seen:
                unique.append(item)
                seen.add(key)

        return unique

    def hybrid_search(self, query: str, top_k: int = 1) -> list[dict]:
        semantic_results = self.semantic_search(query, top_k=top_k)
        semantic_results = self.improve_results(semantic_results, query)
        semantic_results = self.deduplicate_results(semantic_results)

        if semantic_results:
            return semantic_results[:top_k]

        keyword_results = self.keyword_search(query, top_k=top_k)
        keyword_results = self.improve_results(keyword_results, query)
        keyword_results = self.deduplicate_results(keyword_results)

        return keyword_results[:top_k]