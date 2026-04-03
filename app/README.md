# AI Document Parser (Arabic + English Supported)

## Overview
This project is an AI-powered document parser that processes PDF, DOCX, and TXT files.  
It intelligently selects a chunking strategy (fixed or dynamic), stores processed content in both SQL and Vector databases, and supports efficient retrieval using a hybrid search approach.

The system is designed to be RAG-ready and optimized for performance using lazy loading techniques.

---

## Features
- Multi-format support (PDF, DOCX, TXT)
- Intelligent chunking (fixed and dynamic)
- Automatic chunking strategy selection
- Arabic language support (including normalization and diacritics handling)
- English and Arabic query support (bilingual retrieval)
- Hybrid retrieval (semantic search with keyword fallback)
- Vector database integration (ChromaDB)
- SQL database storage (SQLite)
- Quote extraction:
  - Arabic: "ماذا قال فلان؟"
  - English: "What did X say?"
- Interactive Streamlit interface
- Benchmark system (performance and retrieval evaluation)
- RAG-ready architecture

---

## Performance Optimizations
- Lazy loading for embedding models (loaded only when needed)
- Cached storage initialization using Streamlit
- Batch embedding for faster processing
- Avoiding reprocessing of previously processed files
- Optional fast demo mode for large documents

---

## Hardware Limitations

The system performance is constrained by the available hardware resources.

This project relies on transformer-based models (such as sentence-transformers), which are computationally intensive and typically benefit from GPU acceleration. However, the current implementation runs on a local machine using CPU-only processing.

As a result:
- Initial model loading may take noticeable time
- Embedding large documents can be slow
- Processing speed is limited by CPU performance and memory

These limitations are expected when running AI models without GPU support.

---

## Optimization Strategy

To address these constraints, the system includes:
- Lazy loading of models to reduce startup time
- Batch processing for embeddings
- Avoiding repeated computation for the same document
- Lightweight retrieval pipeline

---

## Architecture

1. Parsing Layer  
   Extracts text from PDF, DOCX, and TXT files.

2. Chunking Layer  
   Automatically selects between fixed and dynamic chunking based on document structure.

3. Storage Layer  
   - SQLite for structured data storage  
   - ChromaDB for vector embeddings  

4. Retrieval Layer  
   - Semantic search using vector database  
   - Keyword fallback search  
   - Answer extraction (sentence-level and quote extraction)

---

## How to Run

```bash
pip install -r requirements.txt
cd app
streamlit run main.py