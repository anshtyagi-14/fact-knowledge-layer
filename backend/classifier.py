import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Fact, FactRelationship
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class LLMRelationshipResponse(BaseModel):
    relationship_type: str # CORROBORATES, CONTRADICTS, RECONCILED, NEW_FACT
    confidence: float
    reasoning: str
    requires_human_review: bool

def classify_relationship(db: Session, fact_a: Fact, fact_b: Fact):
    # Check if this relationship already exists
    existing = db.query(FactRelationship).filter(
        ((FactRelationship.fact_a_id == fact_a.id) & (FactRelationship.fact_b_id == fact_b.id)) |
        ((FactRelationship.fact_a_id == fact_b.id) & (FactRelationship.fact_b_id == fact_a.id))
    ).first()
    if existing:
        return existing

    # 1. Rule-based checks
    if fact_a.canonical_value is not None and fact_b.canonical_value is not None:
        if fact_a.canonical_unit == fact_b.canonical_unit:
            val_a = float(fact_a.canonical_value)
            val_b = float(fact_b.canonical_value)
            val_diff = abs(val_a - val_b)
            avg_val = (abs(val_a) + abs(val_b)) / 2 or 1
            percent_diff = val_diff / float(avg_val)
            
            same_time = (fact_a.time_start == fact_b.time_start) and (fact_a.time_end == fact_b.time_end) and (fact_a.time_start is not None)
            same_scope = fact_a.scope_segment == fact_b.scope_segment
            
            if same_time and same_scope and percent_diff < 0.005:
                # Deterministic CORROBORATES
                return _save_rel(db, fact_a, fact_b, "CORROBORATES", 1.0, "Exact numeric, time, and scope match.", "rule", False)
            # Otherwise we escalate to LLM

    # 2. LLM Escallation
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "DUMMY_KEY":
         return _save_rel(db, fact_a, fact_b, "UNKNOWN", 0.0, "API Key missing", "hybrid", True)
         
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are a relationship classifier. Analyze these two facts extracted from financial/macroeconomic documents.
    
    Fact A:
    - Subject: {fact_a.subject}
    - Predicate: {fact_a.predicate}
    - Raw Value: {fact_a.raw_value}
    - Time Context: {fact_a.time_raw}
    - Scope Segment: {fact_a.scope_segment}
    - Evidence: {fact_a.evidence_text}
    
    Fact B:
    - Subject: {fact_b.subject}
    - Predicate: {fact_b.predicate}
    - Raw Value: {fact_b.raw_value}
    - Time Context: {fact_b.time_raw}
    - Scope Segment: {fact_b.scope_segment}
    - Evidence: {fact_b.evidence_text}
    
    Determine if they:
    - CORROBORATES: They agree on the same metric for the same time/scope.
    - CONTRADICTS: They disagree on the same metric for the same time/scope.
    - RECONCILED: They seem to disagree, but it's explained by a difference in time, scope, or definition (e.g. Q1 vs Full Year, or Standalone vs Consolidated).
    - NEW_FACT: They are completely unrelated.
    
    Return strictly JSON matching the schema.
    """
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LLMRelationshipResponse,
                temperature=0.0
            )
        )
        data = json.loads(res.text)
        return _save_rel(db, fact_a, fact_b, data["relationship_type"], data["confidence"], data["reasoning"], "llm", data["requires_human_review"])
    except Exception as e:
        print(f"LLM Classification failed for facts {fact_a.id} and {fact_b.id}: {e}")
        return None

def _save_rel(db, fa, fb, rtype, conf, reasoning, method, req_review):
    if conf < 0.6:
        req_review = True
    rel = FactRelationship(
        fact_a_id=fa.id,
        fact_b_id=fb.id,
        relationship_type=rtype,
        confidence=conf,
        reasoning=reasoning,
        classification_method=method,
        requires_human_review=req_review
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel
