# from langchain_community.vectorstores import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings

# embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# vectorstore = Chroma(
#     persist_directory="backend/vector_db",
#     embedding_function=embedding
# )

# # Search
# def query_documents(question, k=5):
#     results = vectorstore.similarity_search(question, k=k)
#     return [{
#         "doc_id": doc.metadata["doc_id"],
#         "page": doc.metadata["page"],
#         "paragraph": doc.metadata["paragraph"],
#         "answer": doc.page_content.strip()
#     } for doc in results]


# # results = vectorstore.similarity_search("Why does Darcy dislike Wickham?", k=1)
# # table_data = []
# # for doc in results:
# #     table_data.append({
# #         "doc_id": doc.metadata["doc_id"],
# #         "page": doc.metadata["page"],
# #         "paragraph": doc.metadata["paragraph"],
# #         "answer": doc.page_content.strip()
# #     })
    
# # print(table_data)


# 

from langchain_community.vectorstores import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain_groq import ChatGroq
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_collection = "documents_chunks"  # same as used in embed.py

# Load embedding model
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key
)

# Connect LangChain to Qdrant
vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=qdrant_collection,
    embeddings=embedding
)

# Set up retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Set up Groq LLM
llm = ChatGroq(
    groq_api_key=groq_key,
    model_name="llama3-8b-8192",
    temperature=0.3
)

# Create QA chain with sources
qa_chain = load_qa_with_sources_chain(llm, chain_type="stuff")

def query_documents(question: str):
    # Retrieve relevant documents
    docs = retriever.get_relevant_documents(question)

    # Run QA with sources
    result = qa_chain.invoke({"input_documents": docs, "question": question})

    # Format results with metadata
    answers = []
    for doc in docs:
        if "source" not in doc.metadata:
            doc.metadata["source"] = doc.metadata.get("doc_id", "unknown")
        metadata = doc.metadata
        answers.append({
            "doc_id": metadata.get("doc_id", "unknown"),
            "page": metadata.get("page", "unknown"),
            "paragraph": metadata.get("paragraph", "unknown"),
            "answer": doc.page_content
        })

    return answers

