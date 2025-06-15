import streamlit as st
import requests
from dotenv import load_dotenv
import os
import pandas as pd
import time

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")

# Upload multiple documents in batches
def upload_documents_batch(files, batch_size=10):
    """Upload files in batches to avoid timeout and size limits"""
    total_files = len(files)
    successful_uploads = 0
    failed_uploads = []
    
    # Process files in batches
    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        st.info(f"Processing batch {i//batch_size + 1}: files {i+1} to {min(i+batch_size, total_files)}")
        
        try:
            multiple_files = [("files", (file.name, file, "application/octet-stream")) for file in batch]
            response = requests.post(f"{API_URL}/upload/", files=multiple_files, timeout=300)  # 5 min timeout
            response.raise_for_status()
            
            result = response.json()
            if result and result.get("status") == "success":
                successful_uploads += result.get('files_processed', len(batch))
                st.success(f"✅ Batch {i//batch_size + 1}: Processed {len(batch)} files")
            else:
                failed_uploads.extend([f.name for f in batch])
                st.error(f"❌ Batch {i//batch_size + 1} failed: {result.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            failed_uploads.extend([f.name for f in batch])
            st.error(f"❌ Batch {i//batch_size + 1} failed: {e}")
        
        # Small delay between batches
        if i + batch_size < total_files:
            time.sleep(1)
    
    return {
        "total_files": total_files,
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads
    }

# Query the documents
def ask_query(query):
    try:
        response = requests.post(f"{API_URL}/query/", json={"query": query})
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
        response = requests.post(f"{API_URL}/themes/", json={"answers": answers})
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

# Enhanced file upload section
st.markdown("### 📁 Document Upload")
st.markdown("*Upload up to 100+ documents (PDF, TXT, PNG, JPG)*")

uploaded_files = st.file_uploader(
    "Choose files", 
    type=["pdf", "txt", "png", "jpg"], 
    accept_multiple_files=True,
    help="Select multiple files. You can upload 75+ documents."
)

if uploaded_files:
    st.info(f"Selected {len(uploaded_files)} files for upload")
    
    # Show file list if more than 10 files
    if len(uploaded_files) > 10:
        with st.expander(f"📋 View all {len(uploaded_files)} selected files"):
            for i, file in enumerate(uploaded_files, 1):
                st.text(f"{i}. {file.name} ({file.size} bytes)")

# Upload configuration
col1, col2 = st.columns(2)
with col1:
    batch_size = st.selectbox("Batch size (files per batch)", [5, 10, 15, 20], index=1)
with col2:
    st.metric("Files Selected", len(uploaded_files) if uploaded_files else 0)

if st.button("📤 Upload All Documents", disabled=not uploaded_files):
    if len(uploaded_files) > 75:
        st.warning(f"You've selected {len(uploaded_files)} files. This may take several minutes.")
    
    with st.spinner(f"Processing {len(uploaded_files)} documents in batches..."):
        upload_result = upload_documents_batch(uploaded_files, batch_size)
    
    # Display results
    st.markdown("### Upload Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Files", upload_result["total_files"])
    with col2:
        st.metric("Successful", upload_result["successful_uploads"], 
                 delta=upload_result["successful_uploads"] - upload_result["total_files"])
    with col3:
        st.metric("Failed", len(upload_result["failed_uploads"]))
    
    if upload_result["failed_uploads"]:
        with st.expander("❌ Failed uploads"):
            for failed_file in upload_result["failed_uploads"]:
                st.text(f"• {failed_file}")
    
    if upload_result["successful_uploads"] > 0:
        st.success(f"✅ Successfully uploaded and processed {upload_result['successful_uploads']} files!")

# Query interface
st.markdown("### 💬 Ask Questions")
query = st.text_input("Ask a question based on the uploaded documents:")

if st.button("🔍 Get Answer", disabled=not query):
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

# Theme synthesis
if st.button("🧠 Summarize Themes"):
    with st.spinner("Synthesizing themes..."):
        themes = get_themes()
    
    if themes:
        st.markdown("## Synthesized Theme Answer")
        theme_text = themes.get("themes", "")
        lines = theme_text.strip().split("\n")
        
        for line in lines:
            if "–" in line:
                theme_title, details = line.split("–", 1)
                st.markdown(f"**{theme_title.strip()} –** {details.strip()}")
            else:
                st.markdown(line.strip())
    else:
        st.warning("Failed to generate themes.")

# Additional info
with st.sidebar:
    st.markdown("### ℹ️ Tips for Large Uploads")
    st.markdown("""
    - **Batch processing**: Files are uploaded in smaller batches
    - **Supported formats**: PDF, TXT, PNG, JPG
    - **File size**: Keep individual files under 200MB
    - **Total time**: Large uploads may take 5-15 minutes
    - **Network**: Ensure stable internet connection
    """)
    
    if "answers" in st.session_state and st.session_state["answers"]:
        st.markdown(f"### 📊 Session Stats")
        st.metric("Queries Made", len(st.session_state["answers"]))