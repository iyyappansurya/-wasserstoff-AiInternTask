import streamlit as st
import requests

API_URL = "https://rag-backend-5z5q.onrender.com"

# Upload multiple documents
def upload_documents(files):
    multiple_files = [("files", (file.name, file, "application/octet-stream")) for file in files]
    response = requests.post(f"{API_URL}/upload", files=multiple_files)
    return response.json()

# Query the documents
def ask_query(query):
    response = requests.post(f"{API_URL}/query", json={"query": query})
    return response.json()

# Get theme synthesis
def get_themes():
    response = requests.get(f"{API_URL}/themes")
    return response.json()

# --- Streamlit UI ---
st.title("📚 RAG Chatbot – AI Intern Task")

# File upload
uploaded_files = st.file_uploader("📁 Upload one or more documents", type=["pdf", "txt", "png", "jpg"], accept_multiple_files=True)

if st.button("📤 Upload Documents") and uploaded_files:
    with st.spinner("Processing documents..."):
        upload_result = upload_documents(uploaded_files)
    st.success(f"✅ Uploaded and processed {upload_result['files_processed']} documents.")

# Query interface
query = st.text_input("💬 Ask a question based on the documents:")
if st.button("🔍 Get Answer") and query:
    with st.spinner("Thinking..."):
        results = ask_query(query)
    for result in results:
        st.markdown(f"**📄 Doc:** {result['doc_id']} – Page {result['page']}, Para {result['paragraph']}")
        st.markdown(f"> {result['answer']}")
        st.markdown("---")

# Thematic summary
if st.button("🧠 Summarize Themes"):
    with st.spinner("Synthesizing themes..."):
        themes = get_themes()
    st.markdown("## 📌 Common Themes")
    st.markdown(themes)
