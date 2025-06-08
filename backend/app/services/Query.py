from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(
    persist_directory="backend/vector_db",
    embedding_function=embedding
)

# Search
results = vectorstore.similarity_search("Why does Darcy dislike Wickham?", k=1)
table_data = []
for doc in results:
    table_data.append({
        "doc_id": doc.metadata["doc_id"],
        "page": doc.metadata["page"],
        "paragraph": doc.metadata["paragraph"],
        "answer": doc.page_content.strip()
    })
    
print(table_data)

