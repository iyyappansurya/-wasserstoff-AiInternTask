import os
import requests
import arxiv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path("backend/data/DocumentsByMe/")
PDF_DIR = BASE_DIR / "papers"
IMG_DIR = BASE_DIR / "images"
TXT_DIR = BASE_DIR / "texts"



for folder in [PDF_DIR, IMG_DIR, TXT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

def download_arxiv_pdfs(query="machine learning", max_pdfs=50):
    search = arxiv.Search(
        query=query,
        max_results=max_pdfs,
        sort_by=arxiv.SortCriterion.Relevance
    )
    for result in search.results():
        filename = f"{result.get_short_id()}.pdf"
        dest_path = PDF_DIR / filename
        if not dest_path.exists():
            pdf_url = result.pdf_url
            try:
                response = requests.get(pdf_url)
                response.raise_for_status()
                with open(dest_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded: {filename}")
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
    print(f"Downloaded up to {max_pdfs} arXiv PDFs to {PDF_DIR}")
    

def download_scanned_images():
    example_images = [
        "https://www.irs.gov/pub/irs-pdf/f1040.pdf",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    ]
    for i in range(5):
        url = example_images[i % len(example_images)]
        dest = IMG_DIR / f"scan_{i+1}.pdf"
        with requests.get(url, stream=True) as r:
            with open(dest, 'wb') as f:
                f.write(r.content)
    print("Downloaded 5 sample scan-like PDFs/images")

def download_gutenberg_books():
    
    gutenberg_books = {
    "Pride and Prejudice": 1342,
    "Frankenstein": 84,
    "The Art of War": 132,
    "Metamorphosis": 5200,
    "The Republic": 1497,
    "Utopia": 2130,
    "The Time Machine": 35,
    "Dracula": 345,
    "War and Peace": 2600,
    "The Prince": 1232
    }
    
    for title, book_id in gutenberg_books.items():
        url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
        filename = TXT_DIR / f"{title.replace(' ', '_')}.txt"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Downloaded: {title}")
        except Exception as e:
            print(f"Failed: {title} – {e}")
            
if __name__ == "__main__":
    # download_arxiv_pdfs()
    # download_scanned_images()
    download_gutenberg_books()