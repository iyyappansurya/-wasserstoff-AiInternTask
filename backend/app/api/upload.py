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
from .supabase import supabase
import uuid
import os
import logging
from dotenv import load_dotenv
from more_itertools import chunked 

load_dotenv()

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@router.post("/")
async def upload_files(files: list[UploadFile] = File(...)):
    logging.info(f"Received {len(files)} files for upload.")
    
    # Add file count validation
    if len(files) > 50:  # Adjust this limit as needed
        logging.warning(f"Large batch detected: {len(files)} files")
    
    saved_files = []
    failed_files = []
    
    for file in files:
        try:
            file_ext = os.path.splitext(file.filename)[1]
            file_id = str(uuid.uuid4())
            unique_filename = f"{file_id}{file_ext}"

            file_bytes = await file.read()
            public_url = upload_to_supabase(file_bytes, unique_filename)

            saved_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "url": public_url,
                "ext": file_ext
            })
            logging.info(f"Successfully uploaded: {file.filename}")
            
        except Exception as e:
            logging.error(f"Failed to upload {file.filename}: {str(e)}")
            failed_files.append({"filename": file.filename, "error": str(e)})

    # Continue with processing...
    chunks = []
    for f in saved_files:
        try:
            logging.info(f"Processing file: {f['filename']} (ID: {f['file_id']})")
            doc_chunks = processDocuments.process_file_from_url(f["url"], f["file_id"], f["ext"])
            chunks.extend(doc_chunks)
        except Exception as e:
            logging.error(f"Failed to process {f['filename']}: {str(e)}")

    try:
        embed.embed_chunks(chunks)
        return {
            "status": "success",
            "files_processed": len(saved_files),
            "chunks_embedded": len(chunks),
            "failed_files": failed_files
        }
    except Exception as e:
        return {
            "status": "error",
            "files_processed": len(saved_files),
            "message": "Failed during embedding",
            "details": str(e),
            "failed_files": failed_files
        }
        

def upload_to_supabase(file: bytes, filename: str, bucket: str = "user-uploads") -> str:
    try:
        response = supabase.storage.from_(bucket).upload(
            path=filename,
            file=file,
            file_options={"content-type": "application/octet-stream"}
        )

        if hasattr(response, "error") and response.error:
            raise Exception(f"Upload failed: {response.error.message}")

        public_url = supabase.storage.from_(bucket).get_public_url(filename)
        return public_url
    except Exception as e:
        logging.error(f"Supabase upload error for {filename}: {str(e)}")
        raise