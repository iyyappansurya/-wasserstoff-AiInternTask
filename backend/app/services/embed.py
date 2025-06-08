from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import json

# Load chunks
with open("backend/data/chunk_output/all_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"🔹 Loaded {len(chunks)} chunks.")

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Convert to LangChain Documents
docs = [
    Document(page_content=chunk["text"], metadata=chunk["metadata"])
    for chunk in chunks
]

# Create empty Chroma DB
vectorstore = Chroma(
    embedding_function=embedding,
    persist_directory="backend/vector_db"
)

# Batch insertion
batch_size = 128
for i in range(0, len(docs), batch_size):
    batch_docs = docs[i:i + batch_size]
    vectorstore.add_documents(batch_docs)
    print(f"✅ Embedded and stored batch {i // batch_size + 1} of {len(docs) // batch_size + 1}")

vectorstore.persist()
print("✅ All embeddings stored in ChromaDB!")
