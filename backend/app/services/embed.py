# from langchain_community.vectorstores import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.docstore.document import Document
# import json

# Load chunks
# with open("backend/data/chunk_output/all_chunks.json", "r", encoding="utf-8") as f:
#     chunks = json.load(f)

# print(f"🔹 Loaded {len(chunks)} chunks.")

# embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# # Convert to LangChain Documents
# docs = [
#     Document(page_content=chunk["text"], metadata=chunk["metadata"])
#     for chunk in chunks
# ]

# # Create empty Chroma DB
# vectorstore = Chroma(
#     embedding_function=embedding,
#     persist_directory="backend/vector_db"
# )

# # Batch insertion
# batch_size = 128
# for i in range(0, len(docs), batch_size):
#     batch_docs = docs[i:i + batch_size]
#     vectorstore.add_documents(batch_docs)
#     print(f"✅ Embedded and stored batch {i // batch_size + 1} of {len(docs) // batch_size + 1}")

# vectorstore.persist()
# print("✅ All embeddings stored in ChromaDB!")

# def embed_chunks(chunks):
#     from langchain_community.vectorstores import Chroma
#     from langchain.docstore.document import Document
#     from langchain_huggingface import HuggingFaceEmbeddings

#     docs = [
#         Document(page_content=chunk["text"], metadata=chunk["metadata"])
#         for chunk in chunks
#     ]

#     embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
#     vectorstore = Chroma(
#         embedding_function=embedding,
#         persist_directory="backend/vector_db"
#     )

#     vectorstore.add_documents(docs)
#     vectorstore.persist()

import os
import logging
from dotenv import load_dotenv
from langchain_community.vectorstores import Qdrant
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from more_itertools import chunked
import glob

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "documents_chunks"

os.environ["HF_HOME"] = "/tmp/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/tmp/hf_cache"
os.environ["HUGGINGFACE_HUB_CACHE"] = "/tmp/hf_cache"
BATCH_SIZE = 100  # Adjust this based on available memory

def embed_chunks(chunks):
    logging.info(f"Starting embedding for {len(chunks)} chunks...")

    try:
        if not chunks:
            logging.warning("No chunks provided for embedding.")
            return {"status": "error", "message": "No chunks to embed."}

        # Clean up any .lock files that may prevent downloading
        for lock in glob.glob("/tmp/hf_cache/**/*.lock", recursive=True):
            os.remove(lock)
        # embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2",cache_folder="/tmp/hf_cache")
        embedding_model = HuggingFaceEmbeddings(model_name="./app/local_model/all-MiniLM-L6-v2/")
        
        qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        # Ensure collection exists
        try:
            qdrant_client.get_collection(QDRANT_COLLECTION)
        except Exception:
            qdrant_client.recreate_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logging.info(f"Collection '{QDRANT_COLLECTION}' created.")

        vectorstore = Qdrant(
            client=qdrant_client,
            collection_name=QDRANT_COLLECTION,
            embeddings=embedding_model
        )

        total_batches = (len(chunks) - 1) // BATCH_SIZE + 1
        for batch_idx, chunk_batch in enumerate(chunked(chunks, BATCH_SIZE), start=1):
            docs = [
                Document(page_content=chunk["text"], metadata=chunk["metadata"])
                for chunk in chunk_batch
            ]
            vectorstore.add_documents(docs)
            logging.info(f"Embedded batch {batch_idx}/{total_batches} ({len(docs)} docs)")

        logging.info("✅ All chunks embedded successfully.")
        return {"status": "success", "chunks_embedded": len(chunks)}

    except Exception as e:
        logging.error(f"Embedding failed: {str(e)}")
        return {"status": "error", "message": str(e)}
