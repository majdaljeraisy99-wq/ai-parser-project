import sqlite3
import chromadb
from utils import normalize_text, contains_diacritics


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class StorageManager:
    def __init__(self, sqlite_path="../data/documents.db", chroma_path="../data/chroma_db"):
        self.conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.model = None
        self.chroma_client = None
        self.collection = None
        self.sqlite_path = sqlite_path
        self.chroma_path = chroma_path

        self._create_tables()

    def get_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(MODEL_NAME)
        return self.model

    def get_collection(self):
        if self.collection is None:
            if self.chroma_client is None:
                self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(name="documents")
        return self.collection

    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_type TEXT,
            pages INTEGER,
            language TEXT,
            chunking_strategy TEXT,
            total_chunks INTEGER,
            has_diacritics INTEGER
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_index INTEGER,
            original_text TEXT,
            normalized_text TEXT,
            language TEXT,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
        """)

        self.conn.commit()

    def clear_document_data(self):
        self.cursor.execute("DELETE FROM chunks")
        self.cursor.execute("DELETE FROM documents")
        self.conn.commit()

        try:
            collection = self.get_collection()
            all_items = collection.get()
            ids = all_items.get("ids", [])
            if ids:
                collection.delete(ids=ids)
        except Exception:
            pass

    def save_document(self, metadata: dict, chunking_strategy: str, total_chunks: int, text: str) -> int:
        self.cursor.execute("""
        INSERT INTO documents (
            file_name, file_type, pages, language, chunking_strategy, total_chunks, has_diacritics
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata["file_name"],
            metadata["file_type"],
            metadata["pages"],
            metadata["language"],
            chunking_strategy,
            total_chunks,
            1 if contains_diacritics(text) else 0
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    def save_chunks(self, document_id: int, chunks: list, language: str):
        model = self.get_model()
        collection = self.get_collection()

        embeddings = model.encode(
            chunks,
            batch_size=8,
            show_progress_bar=False
        ).tolist()

        for i, chunk in enumerate(chunks):
            normalized = normalize_text(chunk, keep_diacritics=False)

            self.cursor.execute("""
            INSERT INTO chunks (document_id, chunk_index, original_text, normalized_text, language)
            VALUES (?, ?, ?, ?, ?)
            """, (document_id, i, chunk, normalized, language))

            chunk_id = f"{document_id}_{i}"

            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embeddings[i]],
                metadatas=[{
                    "document_id": document_id,
                    "chunk_index": i,
                    "language": language
                }]
            )

        self.conn.commit()

    def get_all_chunks(self):
        self.cursor.execute("""
        SELECT original_text FROM chunks ORDER BY document_id, chunk_index
        """)
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def get_document_summary(self):
        self.cursor.execute("""
        SELECT file_name, file_type, pages, language, chunking_strategy, total_chunks, has_diacritics
        FROM documents
        ORDER BY id DESC LIMIT 1
        """)
        row = self.cursor.fetchone()
        if not row:
            return None

        return {
            "file_name": row[0],
            "file_type": row[1],
            "pages": row[2],
            "language": row[3],
            "chunking_strategy": row[4],
            "total_chunks": row[5],
            "has_diacritics": bool(row[6])
        }