# Wasserstoff AI Intern Task - Document Chatbot

This repository contains a document-based chatbot built using FastAPI, Qdrant, HuggingFace, and Streamlit.Backend deployed in HuggingFace and Frontend in Streamlit Cloud. It was developed as part of an internship assignment to handle 75+ uploaded documents and provide the following functionality:

- Upload multiple files (PDFs, images, or text)
- Process, chunk, and embed document content
- Store embeddings in Qdrant
- Answer user queries with citations
- Summarize key themes across documents

The system is designed to be efficient, modular, and responsive, even when processing large batches of documents.

## Features

- Multi-file upload and background-safe processing
- OCR support for images and scanned PDFs
- HuggingFace embeddings for fast semantic search
- Qdrant vector store for retrieval
- Supabase storage for file persistence
- Citation-based answers and theme summarization using Groq LLaMA
- Streamlit UI for easy interaction

---

## Repository Structure

### frontend/
- `streamlit_app.py`: The main frontend script. Handles file upload, query interface, and polling the backend for processing status.
- `helpers.py`: Contains helper functions used by the frontend for polling or formatting results. (future)

### backend/
- `main.py`: Entrypoint for FastAPI. Includes routing and status tracking.
- `api/`
  - `upload.py`: Handles the file upload route. Files are uploaded to Supabase, then processed and embedded.
  - `query.py`: Accepts a query string and performs a similarity search against Qdrant.
  - `themes.py`: Synthesizes document themes from extracted answers using the Groq LLaMA model.
  - `status.py`: Used to monitor the status of file processing and embedding.
- `services/`
  - `getData.py`: (Optional) Can download data from external sources like arXiv or Gutenberg if used.
  - `processDocuments.py`: Handles file parsing, OCR, text extraction, and chunking.
  - `embed.py`: Embeds chunks using HuggingFace and stores them in Qdrant.
  - `Query.py`: Used to perform similarity search against Qdrant.
  - `themeSummarize.py`: Invokes Groq’s LLaMA API to synthesize high-level themes from the documents.
- `supabase_client.py`: Utility to upload files to Supabase Storage and retrieve public URLs.

### data/
- Local temporary files and chunked data saved here (during development).
- Can be ignored if fully using Supabase for storage.

---

## Setup Instructions

### 1. Clone the repository

git clone https://github.com/iyyappansurya/wasserstoff-AiInternTask
cd wasserstoff-AiInternTask

### 2. Install Requirements

pip install -r requirements.txt

### 3. Environment Varibles (.env)

SUPABASE_URL=<your_supabase_url>
SUPABASE_API_KEY=<your_api_key>
QDRANT_URL=<your_qdrant_url>
QDRANT_API_KEY=<your_qdrant_api_key>


### 4. Run the backend and frontend

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

cd frontend
streamlit run streamlit_app.py

### Future Improvements

Move embedding to a true background queue (Celery/Redis)

Add authentication for multi-user support

Improve theme summarization with prompt chaining

Replace polling with WebSockets for real-time UI updates

Clean up temporary file artifacts and status files

