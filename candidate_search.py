import os
import requests
from pdf_to_context import extract_money_contexts
from context_to_json import convert_contexts

TEMP_DIR = "./tmp_pdfs"
os.makedirs(TEMP_DIR, exist_ok=True)

def download_pdf(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()

    filename = os.path.join(TEMP_DIR, url.split("/")[-1] or "document.pdf")
    with open(filename, "wb") as f:
        f.write(response.content)

    return filename

PDF_URLS = [
    "https://ia601305.us.archive.org/28/items/TheUSIntelligenceCommunity/Doc%2034-NIP%20Budget%20%282012%29.pdf",
    "https://www.govinfo.gov/content/pkg/CRPT-118hrpt162/pdf/CRPT-118hrpt162.pdf",
    "https://www.cbo.gov/system/files/2023-11/hr3932.pdf",
    "https://www.congress.gov/crs_external_products/R/PDF/R44381/R44381.11.pdf"
]

if __name__ == "__main__":
    for url in PDF_URLS:
        print(f"⬇️ Downloading: {url}")
        pdf_path = download_pdf(url)

        contexts = extract_money_contexts(pdf_path)
        convert_contexts(contexts, pdf_path)
