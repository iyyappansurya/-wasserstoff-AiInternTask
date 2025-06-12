from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import json

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

from langchain_community.vectorstores import Qdrant
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import os
from dotenv import load_dotenv
load_dotenv()

# Get from your environment or .env
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "document_chunks"

def embed_chunks(chunks):
    docs = [
        Document(page_content=chunk["text"], metadata=chunk["metadata"])
        for chunk in chunks
    ]

    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create Qdrant client
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    # Create collection if not exists
    try:
        qdrant_client.get_collection(QDRANT_COLLECTION)
    except Exception:
        qdrant_client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    # Store embeddings in Qdrant
    vectorstore = Qdrant(
        client=qdrant_client,
        collection_name=QDRANT_COLLECTION,
        embeddings=embedding
    )

    vectorstore.add_documents(docs)
    print("✅ Embedded and stored documents in Qdrant.")
