import re
import spacy
from nltk.tokenize import sent_tokenize
from pypdf import PdfReader #TODO: Use Fitz rather than pypdf (better formatting of pdfs)

# ---------------------------
# CONFIGURATION
# ---------------------------
# Change this number to adjust how many sentences of context you want
CONTEXT_WINDOW = 1    # 1 = before + after; 2 = wider context; etc.

# ---------------------------
# Load spaCy model once
# ---------------------------
nlp = spacy.load("en_core_web_sm")

# Entities of interest
ENTITIES = ["MONEY", "PERCENT", "CARDINAL", "QUANTITY"] 

# Keywords
KEYWORDS = ["budget", "fiscal", "spend", "alloc"]

# ---------------------------
# Strict fallback money regex
# ---------------------------

money_regex = re.compile(
    r"""
    (?<!\w)  # not part of another word

    (?: 
        # $xxx with optional unit
        \$\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*(?:k|m|b|bn|million|billion|thousand))?
        
        # number followed by unit
        | \d{1,3}(?:,\d{3})*(?:\.\d+)?\s+(?:USD|dollars?|k|m|b|bn|million|billion|thousand)
    )

    (?=$|\b|[.,;:])  # boundary/punctuation
    """,
    re.IGNORECASE | re.VERBOSE
) # TODO: Fix regex it isn't working (or maybe it is and you need to check if it's working)


# ---------------------------
# PDF → text extraction
# ---------------------------
def _extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# ---------------------------
# Detect if a sentence mentions money
# ---------------------------
def _is_money_sentence(sentence: str):
    # 1. spaCy MONEY entities
    doc = nlp(sentence)

    # return true if spaCy detected money mention or regex detected money
    # or keyword in the sentence
    return any(ent.label_ in ENTITIES for ent in doc.ents) \
        or money_regex.search(sentence) \
        or any(keyword.lower() in sentence.lower() for keyword in KEYWORDS)

# ---------------------------
# Build variable-sized context windows
# ---------------------------
def _build_context(sentences, index):
    start = max(0, index - CONTEXT_WINDOW)
    end = min(len(sentences), index + CONTEXT_WINDOW + 1)
    return " ".join(sentences[start:end])

# ---------------------------
# Process a PDF → return contexts
# ---------------------------
def extract_money_contexts(pdf_path):
    print(f"Processing PDF: {pdf_path}")

    # Step 1: Extract text
    text = _extract_text_from_pdf(pdf_path)

    # Step 2: Sentence split
    sentences = sent_tokenize(text)

    # Step 3: Identify money sentences
    money_indices = [i for i, s in enumerate(sentences) if _is_money_sentence(s)]

    # Step 4: Build contexts
    contexts = [_build_context(sentences, i) for i in money_indices]

    return contexts