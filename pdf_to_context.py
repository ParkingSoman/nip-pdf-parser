

import json
import re
from nltk.tokenize import sent_tokenize
import spacy
from bs4 import BeautifulSoup  # ⚠️ Ensure bs4 is installed

CONTEXT_WINDOW = 5
nlp = spacy.load("en_core_web_sm")
ENTITIES = ["MONEY", "PERCENT", "CARDINAL", "QUANTITY"]
KEYWORDS = ["budget", "fiscal", "spend", "alloc"]
money_regex = re.compile(
    r"(?:\$|USD)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:k|m|b|bn|thousand|million|billion)?\b",
    re.IGNORECASE,
)

def _is_money_sentence(sentence: str):
    doc = nlp(sentence)
    s = sentence.lower()
    return (
        any(ent.label_ in ENTITIES for ent in doc.ents)
        or money_regex.search(sentence)
        or any(k in s for k in KEYWORDS)
    )

def _parse_table_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    table_rows = soup.find_all("tr")
    if not table_rows:
        return rows
    
    # Extract headers
    header_cells = table_rows[0].find_all(["td", "th"])
    headers = [h.get_text(" ", strip=True) or f"Col{i+1}" for i, h in enumerate(header_cells)]
    
    # Extract data rows
    for tr in table_rows[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if not cells:
            continue
        pairs = []
        for i, cell in enumerate(cells):
            header = headers[i] if i < len(headers) else f"Col{i+1}"
            pairs.append(f"{header}: {cell}")
        rows.append("; ".join(pairs))
    return rows

def extract_money_contexts_from_mineru(json_path: str):
    with open(json_path, "r") as f:
        data = json.load(f)
    
    pages_text = {}
    pages_tables = {}
    
    # Separate text and tables
    for obj in data:
        page = obj.get("page_idx")
        if page is None:
            continue
        if obj.get("type") == "text":
            pages_text.setdefault(page, []).append(obj.get("text", "").strip())
        elif obj.get("type") == "table":
            pages_tables.setdefault(page, [])
            rows = _parse_table_html(obj.get("table_body", ""))
            pages_tables[page].extend(rows)
    
    contexts = []
    
    # Combine all pages that have either text or tables
    all_pages = set(pages_text.keys()) | set(pages_tables.keys())
    
    for page_idx in sorted(all_pages):
        # Process text with context windows
        if page_idx in pages_text:
            sentences = []
            for b in pages_text[page_idx]:
                sentences.extend([s.strip() for s in sent_tokenize(b) if s.strip()])
            
            triggers = [i for i, s in enumerate(sentences) if _is_money_sentence(s)]
            
            if triggers:
                # Merge overlapping windows
                windows = [(max(0, i - CONTEXT_WINDOW), 
                           min(len(sentences), i + CONTEXT_WINDOW + 1)) 
                          for i in triggers]
                
                merged = []
                cur_s, cur_e = windows[0]
                for s, e in windows[1:]:
                    if s <= cur_e:
                        cur_e = max(cur_e, e)
                    else:
                        merged.append((cur_s, cur_e))
                        cur_s, cur_e = s, e
                merged.append((cur_s, cur_e))
                
                # Create contexts from merged windows
                for s, e in merged:
                    block = " ".join(sentences[s:e])
                    
                    # Add tables from same page ONCE per window
                    if page_idx in pages_tables:
                        block += "\nTABLE:\n" + " | ".join(pages_tables[page_idx])
                    
                    contexts.append(f"(Page {page_idx+1})\n{block}")
                
                # Remove this page's tables from dict so we don't process them again
                pages_tables.pop(page_idx, None)
    
    # 🔧 FIX: Process remaining table-only pages (no text triggers)
    for page_idx in sorted(pages_tables.keys()):
        block = "TABLE:\n" + " | ".join(pages_tables[page_idx])
        contexts.append(f"(Page {page_idx+1})\n{block}")
    
    return contexts
