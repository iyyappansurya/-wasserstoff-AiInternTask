# from fastapi import APIRouter, UploadFile, File
# import os
# from app.services import processDocuments, embed
# import shutil
# import uuid

# router = APIRouter()

# UPLOAD_DIR = "backend/data/UploadedDocs"

# os.makedirs(UPLOAD_DIR, exist_ok=True)

# @router.post("/")
# async def upload_file(file: UploadFile = File(...)):
#     file_id = str(uuid.uuid4())
#     file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
    
#     # Process and embed
#     try:
#         chunks = processDocuments.process_file(file_path)
#         embed.embed_chunks(chunks)
#         return {"status": "success", "message": f"Processed and embedded {file.filename}", "chunks": len(chunks)}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}


# from fastapi import APIRouter, UploadFile, File
# from app.services import processDocuments, embed
# import uuid
# import os
# from .supabase_client import supabase

# router = APIRouter()

# @router.post("/")
# async def upload_files(files: list[UploadFile] = File(...)):
#     saved_files = []
#     for file in files:
#         file_ext = os.path.splitext(file.filename)[1]
#         file_id = str(uuid.uuid4())
#         save_path = f"backend/data/uploads/{file_id}{file_ext}"
#         with open(save_path, "wb") as buffer:
#             buffer.write(await file.read())
#         saved_files.append({"file_id": file_id, "filename": file.filename, "path": save_path})

#     # Process and embed all documents
#     chunks = []
#     for f in saved_files:
#         doc_chunks = processDocuments.process_file(f["path"], f["file_id"])
#         chunks.extend(doc_chunks)

#     embed.embed_chunks(chunks)
#     return {"status": "success", "files_processed": len(saved_files)}



# def upload_to_supabase(file: bytes, filename: str, bucket: str = "user-uploads") -> str:
#     response = supabase.storage.from_(bucket).upload(path=filename, file=file, file_options={"content-type": "application/octet-stream"}, upsert=True)

#     if response.get("error"):
#         raise Exception(f"Upload failed: {response['error']['message']}")

#     public_url = supabase.storage.from_(bucket).get_public_url(filename)
#     return public_url


from fastapi import APIRouter, UploadFile, File
from app.services import processDocuments, embed
from .supabase_client import supabase
import uuid
import tempfile
import os
from dotenv import load_dotenv
load_dotenv()


router = APIRouter()

@router.post("/")
async def upload_files(files: list[UploadFile] = File(...)):
    saved_files = []
    for file in files:
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        unique_filename = f"{file_id}{file_ext}"

        # Read file content into bytes
        file_bytes = await file.read()

        # Upload to Supabase Storage
        public_url = upload_to_supabase(file_bytes, unique_filename)

        saved_files.append({
            "file_id": file_id,
            "filename": file.filename,
            "url": public_url,
            "ext": file_ext
        })

    # Process and embed
    chunks = []
    for f in saved_files:
        doc_chunks = processDocuments.process_file_from_url(f["url"], f["file_id"], f["ext"])
        chunks.extend(doc_chunks)

    embed.embed_chunks(chunks)
    return {"status": "success", "files_processed": len(saved_files)}

def upload_to_supabase(file: bytes, filename: str, bucket: str = "user-uploads") -> str:
    response = supabase.storage.from_(bucket).upload(
        path=filename,
        file=file,
        file_options={"content-type": "application/octet-stream"},
        upsert=True
    )

    if response.get("error"):
        raise Exception(f"Upload failed: {response['error']['message']}")

    public_url = supabase.storage.from_(bucket).get_public_url(filename)
    return public_url
