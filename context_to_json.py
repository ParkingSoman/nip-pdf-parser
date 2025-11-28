import json
import re
from datetime import datetime
from pypdf import PdfReader
import requests
import traceback

# Debug control
DEBUG = False
def debug(*args): 
    if DEBUG: 
        print(*args)

SYSTEM_PROMPT = """
You extract structured budget information from text.

Given a context and a fallback date, return ONLY:
{
  "date": "...",
  "date_source": "provided" | "inferred" | "unknown",
  "agency": "...",
  "function": "...",
  "amount": "...",
  "budget_type": "Increase" | "Decrease" | "Total Budget",
  "context": "..."
}

Rules:
- First, use a date inside the context (date_source="provided")
- Else use the fallback date (date_source="inferred")
- If neither: "date": "Unknown", "date_source": "unknown"
- If no agency OR amount exists → {"skip": true}
- Return ONLY valid JSON.
"""

DATE_INFER_SYSTEM_PROMPT = """
Infer the document year from this excerpt.

Return ONLY:
{
  "date": "...",
  "date_source": "inferred" | "unknown"
}

Rules: choose explicit or strongly implied years only.
If unsure → Unknown.
Valid range: 1900-2050.
Always return valid JSON.
"""

MAX_DATE_WORDS = 300

def call_ollama_api(system_prompt: str, user_prompt: str, model="llama3.1:8b"):
    url = "http://localhost:11434/api/generate"

    full_prompt = (
        f"<|system|>\n{system_prompt}\n"
        f"<|user|>\n{user_prompt}\n"
        f"<|assistant|>\n"
    )

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        if not response.ok:
            return ""
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        print("[ERROR] Ollama call failed:", e)
        return ""

def infer_date_from_pdf_first_words(pdf_path: str, model="llama3.1:8b"):
    reader = PdfReader(pdf_path)
    words = []
    
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_words = re.findall(r"\S+", page_text)
        words.extend(page_words)
        if len(words) >= MAX_DATE_WORDS:
            break

    if not words:
        return None

    snippet = " ".join(words[:MAX_DATE_WORDS])

    raw = call_ollama_api(DATE_INFER_SYSTEM_PROMPT, snippet, model)
    try:
        data = json.loads(raw)
    except:
        return None

    year = data.get("date")
    if year and year not in ["Unknown", None]:
        print(f"📌 Inferred document year: {year}")
        return year

    return None

def convert_contexts(contexts: list[str], pdf_path: str):
    print(f"📊 Extracting budget data from {pdf_path} ...")

    inferred_year = infer_date_from_pdf_first_words(pdf_path)
    fallback_date = inferred_year or "Unknown"
    fallback_source = "inferred" if inferred_year else "unknown"

    results = []

    for ctx in contexts:
        user_prompt = (
            f"Fallback Date: {fallback_date}\n"
            f"Fallback Date Source: {fallback_source}\n"
            f"Context:\n{ctx}"
        )

        raw = call_ollama_api(SYSTEM_PROMPT, user_prompt)

        try:
            data = json.loads(raw)
        except:
            debug("[PARSE ERROR]", raw)
            continue

        if data.get("skip"):
            continue

        data["context"] = ctx
        results.append(data)

    out_file = pdf_path.split("/")[-1].replace(".pdf", ".json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"✅ Saved → {out_file}")
