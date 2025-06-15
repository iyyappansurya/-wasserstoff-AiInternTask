import streamlit as st
import requests
from dotenv import load_dotenv
import os
import pandas as pd
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")

# Optimized upload function with concurrent batches
def upload_documents_concurrent(files, batch_size=5, max_workers=2):
    """Upload files using concurrent batches for better performance"""
    total_files = len(files)
    results = []
    
    # Create batches
    batches = [files[i:i + batch_size] for i in range(0, total_files, batch_size)]
    
    def upload_batch(batch_info):
        batch_idx, batch = batch_info
        try:
            st.info(f"🔄 Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} files)")
            
            multiple_files = [("files", (file.name, file, "application/octet-stream")) for file in batch]
            
            # Use shorter timeout and add retry logic
            for attempt in range(2):  # 2 attempts
                try:
                    response = requests.post(
                        f"{API_URL}/upload/", 
                        files=multiple_files, 
                        timeout=120  # 2 minute timeout instead of 5
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get("status") == "success":
                        st.success(f"✅ Batch {batch_idx + 1}: {result.get('files_processed', len(batch))} files processed")
                        return {
                            "batch_idx": batch_idx,
                            "success": True,
                            "files_processed": result.get('files_processed', len(batch)),
                            "timing": result.get('timing', {}),
                            "details": result.get('details', {})
                        }
                    break
                    
                except requests.exceptions.Timeout:
                    if attempt == 0:
                        st.warning(f"⏱️ Batch {batch_idx + 1} timeout, retrying...")
                        continue
                    else:
                        raise
                        
        except Exception as e:
            st.error(f"❌ Batch {batch_idx + 1} failed: {str(e)}")
            return {
                "batch_idx": batch_idx,
                "success": False,
                "error": str(e),
                "files": [f.name for f in batch]
            }
    
    # Process batches with limited concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        batch_futures = [
            executor.submit(upload_batch, (i, batch)) 
            for i, batch in enumerate(batches)
        ]
        
        for future in batch_futures:
            result = future.result()
            results.append(result)
    
    return results

# Quick upload option
def upload_documents_quick(files):
    """Quick upload endpoint - returns immediately"""
    try:
        multiple_files = [("files", (file.name, file, "application/octet-stream")) for file in files]
        response = requests.post(f"{API_URL}/upload/quick", files=multiple_files, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Quick upload failed: {e}")
        return None

# Query and themes functions (unchanged)
def ask_query(query):
    try:
        response = requests.post(f"{API_URL}/query/", json={"query": query})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Query failed: {e}")
        return None

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
st.title("📚 RAG Chatbot – AI Intern Task (Optimized)")

# Performance metrics in sidebar
with st.sidebar:
    st.markdown("### ⚡ Performance Mode")
    upload_mode = st.radio(
        "Upload Strategy:",
        ["Concurrent Batches", "Quick Upload", "Sequential (Original)"],
        help="""
        - **Concurrent**: Process multiple batches simultaneously (faster)
        - **Quick**: Upload and return immediately, process in background
        - **Sequential**: Original method (slower but reliable)
        """
    )
    
    if upload_mode == "Concurrent Batches":
        batch_size = st.slider("Batch Size", 3, 15, 5)
        max_workers = st.slider("Concurrent Batches", 1, 3, 2)
    
    st.markdown("### 📊 Upload Tips")
    st.markdown("""
    - **Optimal batch size**: 5-8 files
    - **Expected time**: ~30-60s per batch
    - **File size**: Keep under 10MB each
    - **Formats**: PDF works fastest
    """)

# Initialize session state
if "answers" not in st.session_state:
    st.session_state["answers"] = []
if "upload_history" not in st.session_state:
    st.session_state["upload_history"] = []

# File upload section
st.markdown("### 📁 Document Upload")
uploaded_files = st.file_uploader(
    "Choose files", 
    type=["pdf", "txt", "png", "jpg"], 
    accept_multiple_files=True,
    help="Select multiple files for upload"
)

if uploaded_files:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Selected", len(uploaded_files))
    with col2:
        total_size = sum(file.size for file in uploaded_files) / (1024*1024)  # MB
        st.metric("Total Size", f"{total_size:.1f} MB")
    with col3:
        if upload_mode == "Concurrent Batches":
            estimated_time = (len(uploaded_files) / batch_size) * 45 / max_workers  # seconds
            st.metric("Est. Time", f"{estimated_time:.0f}s")

# Upload buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Upload Documents", disabled=not uploaded_files, type="primary"):
        start_time = time.time()
        
        if upload_mode == "Quick Upload":
            with st.spinner("Quick uploading..."):
                result = upload_documents_quick(uploaded_files)
            
            if result:
                st.success(f"✅ Quick upload successful! {result['files_received']} files accepted")
                st.info("📋 Files are being processed in the background")
                
        elif upload_mode == "Concurrent Batches":
            with st.spinner(f"Processing {len(uploaded_files)} files in concurrent batches..."):
                results = upload_documents_concurrent(uploaded_files, batch_size, max_workers)
            
            # Analyze results
            successful_batches = [r for r in results if r.get("success")]
            failed_batches = [r for r in results if not r.get("success")]
            total_processed = sum(r.get("files_processed", 0) for r in successful_batches)
            
            # Display results
            total_time = time.time() - start_time
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Files Processed", total_processed)
            with col2:
                st.metric("Successful Batches", len(successful_batches))
            with col3:
                st.metric("Failed Batches", len(failed_batches))
            with col4:
                st.metric("Total Time", f"{total_time:.1f}s")
            
            # Show timing details for successful batches
            if successful_batches:
                st.success(f"✅ Successfully processed {total_processed} files!")
                
                # Show detailed timing if available
                with st.expander("📊 Performance Breakdown"):
                    timing_data = []
                    for result in successful_batches:
                        if "timing" in result:
                            timing = result["timing"]
                            timing_data.append({
                                "Batch": result["batch_idx"] + 1,
                                "Files": result["files_processed"],
                                "Total Time": timing.get("total_time", "N/A"),
                                "Read Time": timing.get("read_time", "N/A"),
                                "Process Time": timing.get("process_time", "N/A")
                            })
                    
                    if timing_data:
                        df = pd.DataFrame(timing_data)
                        st.dataframe(df, use_container_width=True)
            
            if failed_batches:
                with st.expander("❌ Failed Batches"):
                    for failed in failed_batches:
                        st.error(f"Batch {failed['batch_idx'] + 1}: {failed.get('error', 'Unknown error')}")
        
        else:  # Sequential (original)
            st.warning("Using original sequential upload (slower)")
            # Your original upload logic here

with col2:
    if st.button("📊 Check Upload Status", disabled=not uploaded_files):
        # Add endpoint to check processing status
        st.info("Status checking not implemented yet")

# Query interface
st.markdown("### 💬 Ask Questions")
query = st.text_input("Ask a question based on the uploaded documents:")

if st.button("🔍 Get Answer", disabled=not query):
    with st.spinner("Thinking..."):
        response = ask_query(query)
    
    if response and "results" in response:
        results = response["results"]
        
        table_data = []
        for result in results:
            table_data.append({
                "Document ID": result["doc_id"],
                "Extracted Answer": result["answer"],
                "Citation": f"Page {result['page']}, Para {result['paragraph']}"
            })
            
            st.session_state["answers"].append({
                "doc_id": result["doc_id"],
                "answer": result["answer"]
            })
        
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

# Performance tracking
if st.session_state.get("upload_history"):
    with st.expander("📈 Upload History"):
        st.json(st.session_state["upload_history"])