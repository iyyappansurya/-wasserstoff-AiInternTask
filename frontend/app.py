import streamlit as st
import requests
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")

# Upload multiple documents
def upload_documents(files):
    try:
        multiple_files = [("files", (file.name, file, "application/octet-stream")) for file in files]
        response = requests.post(f"{API_URL}/upload", files=multiple_files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {e}")
        return None

# Query the documents
def ask_query(query):
    try:
        response = requests.post(f"{API_URL}/query", json={"query": query})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Query failed: {e}")
        return None

# Get theme synthesis
def get_themes():
    try:
        answers = st.session_state.get("answers", [])
        if not answers:
            st.warning("No answers to summarize. Please ask a question first.")
            return None
        response = requests.post(f"{API_URL}/themes", json={"answers": answers})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Theme synthesis failed: {e}")
        return None

# --- Streamlit UI ---
st.title("📚 RAG Chatbot – AI Intern Task")


# Initialize session state
if "answers" not in st.session_state:
    st.session_state["answers"] = []
# File upload
uploaded_files = st.file_uploader("📁 Upload one or more documents", type=["pdf", "txt", "png", "jpg"], accept_multiple_files=True)

if st.button("📤 Upload Documents") and uploaded_files:
    with st.spinner("Processing documents..."):
        upload_result = upload_documents(uploaded_files)
    if upload_result and upload_result.get("status") == "success":
        st.success(f"✅ Uploaded and processed {upload_result['files_processed']} file(s).")
    else:
        st.warning(f"Upload failed: {upload_result.get('message', 'Unknown error')}")
        if "details" in upload_result:
            st.error(upload_result["details"])

# Query interface
# query = st.text_input("💬 Ask a question based on the documents:")
# if st.button("🔍 Get Answer") and query:
#     with st.spinner("Thinking..."):
#         response = ask_query(query)
#     if response and "results" in response:
#         results = response["results"]
#         for result in results:
#             st.markdown(f"**📄 Doc:** {result['doc_id']} – Page {result['page']}, Para {result['paragraph']}")
#             st.markdown(f"> {result['answer']}")
#             st.markdown("---")
            
#             st.session_state["answers"].append({
#             "doc_id": result["doc_id"],
#             "answer": result["answer"]
#             })
#     else:
#         st.warning("No answer returned. Please check the backend or input.")

query = st.text_input("Ask a question based on the documents:")
if st.button("Get Answer") and query:
    with st.spinner("Thinking..."):
        response = ask_query(query)
    if response and "results" in response:
        results = response["results"]

        # Build data for the table
        table_data = []
        for result in results:
            table_data.append({
                "Document ID": result["doc_id"],
                "Extracted Answer": result["answer"],
                "Citation": f"Page {result['page']}, Para {result['paragraph']}"
            })

            # Save for later theme synthesis
            st.session_state["answers"].append({
                "doc_id": result["doc_id"],
                "answer": result["answer"]
            })

        # Display as a DataFrame
        st.markdown("### Individual Document Answers")
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

    else:
        st.warning("No answer returned. Please check the backend or input.")

# # Thematic summary
# if st.button("🧠 Summarize Themes"):
#     with st.spinner("Synthesizing themes..."):
#         themes = get_themes()
#     if themes:
#         st.markdown("## 📌 Common Themes")
#         st.markdown(themes.get("themes", "No themes generated."))
#     else:
#         st.warning("Failed to generate themes.")

if st.button("Summarize Themes"):
    with st.spinner("Synthesizing themes..."):
        themes = get_themes()
    if themes:
        st.markdown("## Synthesized Theme Answer (Chat Format)")

        # Assumes the backend returns themes as a string, else parse appropriately
        theme_text = themes.get("themes", "")
        lines = theme_text.strip().split("\n")

        # Format each theme in chat-like style
        for line in lines:
            if "–" in line:
                theme_title, details = line.split("–", 1)
                st.markdown(f"**{theme_title.strip()} –** {details.strip()}")
            else:
                st.markdown(line.strip())
    else:
        st.warning("Failed to generate themes.")
