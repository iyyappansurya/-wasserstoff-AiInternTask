import requests

API_URL = "http://localhost:8000"

def upload_document(file):
    files = {"file": (file.name, file, "application/octet-stream")}
    return requests.post(f"{API_URL}/upload", files=files)

def ask_query(query):
    response = requests.post(f"{API_URL}/query/", json={"query": query})
    print("🔍 Response JSON:", response.text)  # Add this to debug
    return response.json()
def get_themes():
    return requests.post(f"{API_URL}/themes").json()
