import re
import os
import json
from datetime import date
from rapidfuzz import fuzz, process
from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Entity, Fact

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# --- Deterministic Maps ---
SCALE_MAP = {
    'cr': 1e7, 'crore': 1e7, 'crores': 1e7,
    'lakh': 1e5, 'lakhs': 1e5, 'lac': 1e5, 'lacs': 1e5,
    'mn': 1e6, 'million': 1e6, 'millions': 1e6, 'm': 1e6,
    'bn': 1e9, 'billion': 1e9, 'billions': 1e9, 'b': 1e9,
    'k': 1e3, 'thousand': 1e3, 'thousands': 1e3
}

CURRENCY_SYMBOLS = {
    '₹': 'INR', 'rs': 'INR', 'inr': 'INR', 'rs.': 'INR',
    '$': 'USD', 'usd': 'USD',
    '€': 'EUR', 'eur': 'EUR',
    '%': 'PERCENT', 'percent': 'PERCENT', 'percentage': 'PERCENT'
}

# --- LLM Fallback Schemas ---
class CanonicalValueFallback(BaseModel):
    canonical_value: float | None
    canonical_unit: str | None
    confidence: float

class EntityResolutionFallback(BaseModel):
    canonical_name: str
    entity_type: str # organization | person | place | other
    confidence: float

# --- 1. Value Canonicalization ---
def parse_numeric_value(raw_val: str, predicate: str = ""):
    if not raw_val:
        return None, None
        
    raw_lower = raw_val.lower().replace(',', '')
    
    # 1. Attempt deterministic rule-based parsing
    # Find numbers
    num_match = re.search(r'[-+]?\d*\.\d+|\d+', raw_lower)
    if not num_match:
        return fallback_parse_value(raw_val, predicate)
        
    base_val = float(num_match.group())
    
    # Find scales
    multiplier = 1.0
    for scale_key, scale_val in SCALE_MAP.items():
        # Match whole words to avoid matching "m" in "company"
        if re.search(rf'\b{scale_key}\b', raw_lower):
            multiplier = scale_val
            break
            
    # Find units
    unit = None
    for sym_key, sym_val in CURRENCY_SYMBOLS.items():
        if sym_key in raw_lower or re.search(rf'\b{sym_key}\b', raw_lower):
            unit = sym_val
            break
            
    # Derive common units based on predicate if missing
    if not unit:
        if 'revenue' in predicate.lower() or 'ebitda' in predicate.lower():
            unit = 'INR'  # Default assumption for Indian context if not stated, but risky.
        elif 'shipment' in predicate.lower() or 'count' in predicate.lower():
            unit = 'COUNT'
        elif 'area' in predicate.lower() or 'sqft' in predicate.lower():
            unit = 'SQFT'
            
    # If we confidently parsed the number, return it
    if base_val is not None:
        return base_val * multiplier, unit
        
    # 2. LLM Fallback if regex fails completely
    return fallback_parse_value(raw_val, predicate)

def fallback_parse_value(raw_val: str, predicate: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "DUMMY_KEY":
        return None, None
    client = genai.Client(api_key=api_key)
    prompt = f"Convert the following raw value to a base number and unit. Raw value: '{raw_val}'. Context predicate: '{predicate}'. Example: 'Rs. 8,142 Cr' -> value: 81420000000, unit: 'INR'. Return strictly JSON."
    
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CanonicalValueFallback,
                temperature=0.0
            )
        )
        data = json.loads(res.text)
        return data.get("canonical_value"), data.get("canonical_unit")
    except Exception as e:
        print(f"LLM Fallback failed for value '{raw_val}': {e}")
        return None, None

# --- 2. Date/Time Canonicalization ---
def canonicalize_time_context(time_period_type: str, time_raw: str):
    if not time_raw:
        return None, None
        
    raw_lower = time_raw.lower()
    start_date = None
    end_date = None
    
    # Rule for Indian FY: "FY24" -> 2023-04-01 to 2024-03-31
    fy_match = re.search(r'fy(\d{2})', raw_lower)
    if fy_match:
        year = int(fy_match.group(1)) + 2000
        start_date = date(year - 1, 4, 1)
        end_date = date(year, 3, 31)
        
        # Check if it's a specific quarter
        q_match = re.search(r'q(\d)', raw_lower)
        if q_match:
            quarter = int(q_match.group(1))
            if quarter == 1: # Apr-Jun
                end_date = date(year - 1, 6, 30)
            elif quarter == 2: # Jul-Sep
                start_date = date(year - 1, 7, 1)
                end_date = date(year - 1, 9, 30)
            elif quarter == 3: # Oct-Dec
                start_date = date(year - 1, 10, 1)
                end_date = date(year - 1, 12, 31)
            elif quarter == 4: # Jan-Mar
                start_date = date(year, 1, 1)
                
    return start_date, end_date

# --- 3. Entity Resolution ---
def resolve_entity(db: Session, raw_subject: str) -> str:
    # 1. Fetch existing entities
    existing_entities = db.query(Entity).all()
    
    # 2. Fuzzy Match against canonical names and aliases
    best_match = None
    best_score = 0
    
    for entity in existing_entities:
        # Check canonical name
        score = fuzz.token_sort_ratio(raw_subject.lower(), entity.canonical_name.lower())
        if score > best_score:
            best_score = score
            best_match = entity
            
        # Check aliases
        if entity.aliases:
            for alias in entity.aliases:
                alias_score = fuzz.token_sort_ratio(raw_subject.lower(), alias.lower())
                if alias_score > best_score:
                    best_score = alias_score
                    best_match = entity
                    
    # Threshold for deterministic match
    if best_score > 88 and best_match:
        return best_match.id
        
    # 3. If no deterministic match, use LLM to canonicalize the new entity name
    api_key = os.getenv("GEMINI_API_KEY")
    canonical_name = raw_subject
    entity_type = "other"
    
    if api_key and api_key != "DUMMY_KEY":
        client = genai.Client(api_key=api_key)
        prompt = f"Determine the canonical name and entity type (organization, person, place, other) for the entity '{raw_subject}'. Remove 'The' or prefixes if unnecessary. Return JSON."
        try:
            res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EntityResolutionFallback,
                    temperature=0.0
                )
            )
            data = json.loads(res.text)
            canonical_name = data.get("canonical_name", raw_subject)
            entity_type = data.get("entity_type", "other")
        except Exception as e:
            print(f"Entity LLM Fallback failed for '{raw_subject}': {e}")
            
    # Create new entity
    new_entity = Entity(
        canonical_name=canonical_name,
        entity_type=entity_type,
        aliases=[raw_subject] if raw_subject != canonical_name else []
    )
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity.id

# --- Main Pipeline Execution for Phase 2 ---
def canonicalize_fact(db: Session, fact: Fact):
    print(f"Canonicalizing Fact {fact.id} - Subject: {fact.subject}, Raw Value: {fact.raw_value}")
    
    # 1. Resolve Entity
    if fact.subject and not fact.subject_entity_id:
        fact.subject_entity_id = resolve_entity(db, fact.subject)
        
    # 2. Canonicalize Value
    if fact.value_type == "numeric" and not fact.canonical_value:
        val, unit = parse_numeric_value(fact.raw_value, fact.predicate)
        if val is not None:
            fact.canonical_value = val
        if unit is not None:
            fact.canonical_unit = unit
            
    # 3. Canonicalize Time Context
    if fact.time_raw and not fact.time_start:
        start_d, end_d = canonicalize_time_context(fact.time_period_type, fact.time_raw)
        if start_d:
            fact.time_start = start_d
        if end_d:
            fact.time_end = end_d
            
    db.commit()
