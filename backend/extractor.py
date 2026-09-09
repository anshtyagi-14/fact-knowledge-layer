import os
import json
from google import genai
from google.genai import types
from rapidfuzz import fuzz
from schemas import FactExtractionResponse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def get_client():
    api_key = os.getenv("GEMINI_API_KEY", "DUMMY_KEY")
    if api_key != "DUMMY_KEY":
        return genai.Client(api_key=api_key)
    return None

SYSTEM_PROMPT = """You are a precise fact-extraction and reasoning engine. You only report what is explicitly stated in the provided text. You never infer, assume, or add information not present in the source. If uncertain, express that in a confidence score rather than guessing. Output strictly valid JSON matching the given schema, with no other text.
If the evidence text does not clearly support the fact, do not include it. Do not use outside knowledge about this company, country, or topic — reason only from the provided text.
If the chunk contains no extractable facts, return an empty facts array. Do not fabricate a fact to avoid returning an empty result."""

def extract_facts(chunk_text: str, page_number: int, doc_type_hint: str):
    client = get_client()
    if client is None:
        print("Using MOCK Gemini extraction because GEMINI_API_KEY is not set.")
        return {
            "facts": [
                {
                    "subject": "Delhivery",
                    "predicate": "revenue_from_services",
                    "object": None,
                    "raw_value": "Rs. 8,142 Cr",
                    "value_type": "numeric",
                    "time_context": {
                        "period_type": "fiscal_year",
                        "raw": "FY24"
                    },
                    "scope": {
                        "consolidation": "unspecified",
                        "segment": "company-wide"
                    },
                    "evidence_text": "FY24 revenue from services increased to Rs. 8,142 Cr",
                    "confidence_score": 0.98
                }
            ]
        }

    prompt = f"Extract facts from the following text (Page {page_number}, Document Type: {doc_type_hint}):\n\n{chunk_text}"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=FactExtractionResponse,
            temperature=0.0
        ),
    )
    
    return json.loads(response.text)

def verify_evidence(evidence_text: str, source_text: str) -> bool:
    if not evidence_text or not source_text:
        return False
    if evidence_text in source_text:
        return True
    
    score = fuzz.partial_ratio(evidence_text, source_text)
    return score > 85
