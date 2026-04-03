import os
import streamlit as st

from parser import parse_document
from chunking import chunk_document
from storage import StorageManager
from retrieval import Retriever
from benchmark import run_document_benchmark, run_retrieval_benchmark

os.makedirs("../data", exist_ok=True)

st.set_page_config(page_title="AI Document Parser", layout="wide")
st.title("AI-Powered Document Parser")
st.caption("Arabic + English document parsing, chunking, storage, and retrieval")
st.caption("Fast startup mode enabled")

if "processed_file" not in st.session_state:
    st.session_state["processed_file"] = None
if "last_metadata" not in st.session_state:
    st.session_state["last_metadata"] = None
if "last_strategy" not in st.session_state:
    st.session_state["last_strategy"] = None
if "last_chunks" not in st.session_state:
    st.session_state["last_chunks"] = None
if "doc_ready" not in st.session_state:
    st.session_state["doc_ready"] = False


@st.cache_resource
def get_storage():
    return StorageManager()


storage = get_storage()
retriever = Retriever(storage)

uploaded_file = st.file_uploader(
    "ارفع ملف / Upload PDF, DOCX, TXT",
    type=["pdf", "docx", "txt"]
)

if uploaded_file:
    save_path = os.path.join("../data", uploaded_file.name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("تم رفع الملف / File uploaded successfully")

    if st.button("Process Document"):
        current_file = uploaded_file.name

        if st.session_state["processed_file"] == current_file and st.session_state["doc_ready"]:
            st.info("الملف تمت معالجته بالفعل / This file is already processed")
        else:
            parsed = parse_document(save_path)
            text = parsed["text"]
            metadata = parsed["metadata"]

            strategy, chunks = chunk_document(text)

            storage.clear_document_data()
            document_id = storage.save_document(metadata, strategy, len(chunks), text)
            storage.save_chunks(document_id, chunks, metadata["language"])

            st.session_state["processed_file"] = current_file
            st.session_state["last_metadata"] = metadata
            st.session_state["last_strategy"] = strategy
            st.session_state["last_chunks"] = chunks
            st.session_state["doc_ready"] = True

            st.success("تمت المعالجة بنجاح / Document processed successfully")

if st.session_state["doc_ready"] and st.session_state["last_metadata"]:
    metadata = st.session_state["last_metadata"]
    strategy = st.session_state["last_strategy"]
    chunks = st.session_state["last_chunks"]

    st.subheader("نتيجة المعالجة / Processing Result")
    st.write("اسم الملف / File name:", metadata["file_name"])
    st.write("نوع الملف / File type:", metadata["file_type"])
    st.write("عدد الصفحات / Pages:", metadata["pages"])
    st.write("اللغة / Language:", metadata["language"])
    st.write("استراتيجية التقسيم / Chunking strategy:", strategy)
    st.write("عدد المقاطع / Number of chunks:", len(chunks))

    summary = storage.get_document_summary()
    if summary:
        st.write("يحتوي تشكيل / Has Arabic diacritics:", summary["has_diacritics"])

    with st.expander("عرض أول 3 chunks / Show first 3 chunks"):
        for i, chunk in enumerate(chunks[:3]):
            st.markdown(f"**Chunk {i+1}**")
            st.write(chunk[:1000])

    st.divider()
    st.subheader("اسأل عن الملف / Ask about the document")
    query = st.text_input("اكتب سؤالك / Ask your question")

    if st.button("Search"):
        if query.strip():
            results = retriever.hybrid_search(query, top_k=1)

            if results:
                st.success("تم العثور على إجابة / Answer found")
                st.subheader("أفضل إجابة / Best Answer")
                st.info(results[0]["answer"])

                with st.expander("تفاصيل النتيجة / Result details"):
                    st.write("Search method:", results[0]["method"])
                    st.write("Metadata:", results[0]["metadata"])
                    st.write("Source chunk:")
                    st.write(results[0]["full_chunk"])
            else:
                st.warning("ما وجدت إجابة صريحة وواضحة داخل الملف / No clear answer found in the document")
        else:
            st.warning("اكتب سؤال أولًا / Please enter a question first")

    st.divider()
    st.subheader("Benchmark")

    if st.button("Run Benchmark"):
        latest_path = os.path.join("../data", metadata["file_name"])
        doc_metrics = run_document_benchmark(latest_path)

        st.markdown("### Document Benchmark")
        st.json(doc_metrics)

        test_cases_path = "../data/test_cases.json"
        if os.path.exists(test_cases_path):
            retrieval_metrics = run_retrieval_benchmark(test_cases_path)
            st.markdown("### Retrieval Benchmark")
            st.json(retrieval_metrics)
        else:
            st.info("ملف test_cases.json غير موجود داخل data")