# import os
# import fitz  # PyMuPDF
# import pytesseract
# from PIL import Image
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# import spacy
# import uuid
# import json

# nlp = spacy.load("en_core_web_sm")


# def extract_text_from_pdf(pdf_path):
#     doc = fitz.open(pdf_path)
#     pages = []
#     for i, page in enumerate(doc):
#         text = page.get_text("blocks")
#         paragraphs = [block[4] for block in text if block[6] == 0]  # only text blocks
#         formatted = "\n\n".join(paragraphs)
#         pages.append({"page": i + 1, "text": formatted})
#     return pages


# def extract_text_from_txt(txt_path):
#     with open(txt_path, "r", encoding="utf-8") as f:
#         text = f.read()
#     return [{"page": 1, "text": text}]


# def extract_text_from_image(image_path):
#     image = Image.open(image_path)
#     text = pytesseract.image_to_string(image)
#     return [{"page": 1, "text": text}]


# def smart_chunk(text, chunk_size=500, chunk_overlap=50):
#     splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ".", " "])
#     return splitter.split_text(text)


# def chunk_with_metadata(texts, doc_id):
#     chunks = []
#     for page_obj in texts:
#         page_num = page_obj["page"]
#         text = page_obj["text"]
#         paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

#         for para_index, para in enumerate(paragraphs):
#             para_chunks = smart_chunk(para)
#             for chunk_index, chunk in enumerate(para_chunks):
#                 chunk_id = str(uuid.uuid4())
#                 chunks.append({
#                     "id": chunk_id,
#                     "text": chunk,
#                     "metadata": {
#                         "doc_id": doc_id,
#                         "page": page_num,
#                         "paragraph": para_index,
#                         "chunk_index": chunk_index
#                     }
#                 })
#     return chunks


# def process_file(file_path):
#     ext = os.path.splitext(file_path)[-1].lower()
#     doc_id = os.path.basename(file_path)

#     if ext in [".pdf"]:
#         pages = extract_text_from_pdf(file_path)
#     elif ext in [".txt"]:
#         pages = extract_text_from_txt(file_path)
#     elif ext in [".png", ".jpg", ".jpeg"]:
#         pages = extract_text_from_image(file_path)
#     else:
#         raise ValueError(f"Unsupported file type: {ext}")

#     return chunk_with_metadata(pages, doc_id)


# # Example usage:
# if __name__ == "__main__":
#     root_dir = "backend/data/DocumentsByMe"
#     all_chunks = []
#     for subdir, _, files in os.walk(root_dir):
#         for fname in files:
#             fpath = os.path.join(subdir, fname)
#             try:
#                 chunks = process_file(fpath)
#                 all_chunks.extend(chunks)
#                 print(f"Processed {fpath}: {len(chunks)} chunks")
#             except Exception as e:
#                 print(f"Failed to process {fpath}: {e}")

#     print(f"Total chunks created: {len(all_chunks)}")

#     # Save to JSON
#     output_path = "backend/data/chunk_output/all_chunks.json"
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(all_chunks, f, ensure_ascii=False, indent=2)

#     print(f"✅ Chunks saved to {output_path}")


import os
import fitz
import pytesseract
import uuid
import requests
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
import spacy
import tempfile
import logging

nlp = spacy.load("en_core_web_sm")

def download_temp_file(file_url, file_ext):
    response = requests.get(file_url)
    response.raise_for_status()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    with open(tmp_file.name, 'wb') as f:
        f.write(response.content)
    return tmp_file.name

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("blocks")
        paragraphs = [block[4] for block in text if block[6] == 0]
        formatted = "\n\n".join(paragraphs)
        pages.append({"page": i + 1, "text": formatted})
    return pages

def extract_text_from_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{"page": 1, "text": text}]

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return [{"page": 1, "text": text}]

def smart_chunk(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_text(text)

def chunk_with_metadata(texts, doc_id):
    chunks = []
    for page_obj in texts:
        page_num = page_obj["page"]
        text = page_obj["text"]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for para_index, para in enumerate(paragraphs):
            para_chunks = smart_chunk(para)
            for chunk_index, chunk in enumerate(para_chunks):
                chunk_id = str(uuid.uuid4())
                chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        "doc_id": doc_id,
                        "page": page_num,
                        "paragraph": para_index,
                        "chunk_index": chunk_index,
                        "source": f"{doc_id}_page_{page_num}"
                    }
                })
    return chunks

def process_file_from_url(file_url, doc_id, file_ext, max_chunks=None):
    logging.info(f"Downloading and processing: {file_url}")
    temp_path = download_temp_file(file_url, file_ext)

    try:
        if file_ext == ".pdf":
            pages = extract_text_from_pdf(temp_path)
        elif file_ext == ".txt":
            pages = extract_text_from_txt(temp_path)
        elif file_ext in [".png", ".jpg", ".jpeg"]:
            pages = extract_text_from_image(temp_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    finally:
        os.remove(temp_path)

    chunks = chunk_with_metadata(pages, doc_id)
    logging.info(f"Generated {len(chunks)} chunks for {doc_id}")

    if max_chunks and len(chunks) > max_chunks:
        logging.warning(f"Trimming to {max_chunks} chunks due to limit")
        chunks = chunks[:max_chunks]

    return chunks
