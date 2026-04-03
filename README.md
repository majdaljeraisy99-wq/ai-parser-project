
2. **Chunking Layer**  
   Splits content into meaningful segments for better retrieval

3. **Storage Layer**  
   Stores chunks and metadata using SQLite

4. **Retrieval Layer**  
   Performs hybrid search and extracts the most relevant answer

---
Example Queries
ماذا قال الحسود للملك؟
ماذا قال الملك؟
What did the king say?
What happened in the story?
Performance & Design Decision

This project intentionally avoids heavy LLMs to keep the system lightweight and deployable on standard machines.

However, this means:

Processing large documents may take longer
CPU-based execution limits speed compared to GPU systems

This trade-off was chosen to balance simplicity, cost, and deployability

Limitations
Slower processing for large documents
No GPU acceleration
Retrieval is not full generative AI (focused on precision extraction)
Future Improvements
Add GPU acceleration for embeddings
Improve semantic understanding
Add caching for faster repeated queries
Scale storage beyond SQLite
Live Demo
(https://ai-parser-project-djmmjcs62batjs5vfscmeu.streamlit.app/)
## How to Run
```bash
pip install -r requirements.txt
cd app
streamlit run main.py


