import os
from google import genai
from sqlalchemy.orm import Session
from models import Fact
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def generate_embedding(text: str) -> list[float]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "DUMMY_KEY":
        return [0.0] * 768
    client = genai.Client(api_key=api_key)
    res = client.models.embed_content(
        model='models/gemini-embedding-001',
        contents=text
    )
    return res.embeddings[0].values

def embed_fact(db: Session, fact: Fact):
    # As per Section 6, the embedding deliberately excludes the value 
    # to surface contradictions/corroborations of the same metric.
    text_to_embed = f"{fact.subject} | {fact.predicate} | {fact.time_raw} | {fact.scope_segment}"
    embedding = generate_embedding(text_to_embed)
    fact.embedding = embedding
    db.commit()

def find_candidate_pairs(db: Session, fact: Fact, threshold: float = 0.80):
    # using pgvector cosine_distance (which is 1 - cosine_similarity)
    max_distance = 1.0 - threshold
    candidates = db.query(Fact).filter(
        Fact.id != fact.id,
        Fact.embedding.cosine_distance(fact.embedding) < max_distance
    ).all()
    return candidates
