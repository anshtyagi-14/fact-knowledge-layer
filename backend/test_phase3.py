import asyncio
from database import init_db, SessionLocal
from models import Fact, FactRelationship, Document, Chunk
from matcher import embed_fact, find_candidate_pairs
from classifier import classify_relationship

def main():
    print("Initializing Database...")
    init_db()
    db = SessionLocal()
    
    # Let's insert a conflicting fact to test CONTRADICTS logic
    doc = db.query(Document).first()
    chunk = db.query(Chunk).first()
    if doc and chunk:
        fake_fact = Fact(
            document_id=doc.id,
            chunk_id=chunk.id,
            subject="Net foreign direct investment (FDI) inflows",
            predicate="amount",
            raw_value="US$ 10.5 billion",
            canonical_value=10500000000.0,
            canonical_unit="USD",
            value_type="numeric",
            time_raw="a year ago",
            scope_segment="company-wide",
            evidence_text="Dummy contradictory evidence",
            confidence_score=0.99,
            status="verified"
        )
        db.add(fake_fact)
        db.commit()
        print("Inserted dummy fact to force a contradiction.")

    facts = db.query(Fact).all()
    print(f"Generating embeddings for {len(facts)} facts...")
    for fact in facts:
        if not fact.embedding:
            embed_fact(db, fact)
            
    print("Finding candidates and classifying relationships...")
    for fact in facts:
        candidates = find_candidate_pairs(db, fact, threshold=0.85)
        for candidate in candidates:
            # Avoid self-classification or duplicate reverse checks
            if fact.id < candidate.id:
                rel = classify_relationship(db, fact, candidate)
                if rel and rel.relationship_type != "NEW_FACT":
                    print(f"\n--- Relationship Found ---")
                    print(f"Fact A: {fact.raw_value} ({fact.evidence_text})")
                    print(f"Fact B: {candidate.raw_value} ({candidate.evidence_text})")
                    print(f"Type: {rel.relationship_type} (Conf: {rel.confidence}, Review: {rel.requires_human_review})")
                    print(f"Reasoning: {rel.reasoning}")
                    print(f"Method: {rel.classification_method}")

    db.close()
    print("\nPhase 3 Complete.")

if __name__ == "__main__":
    main()
