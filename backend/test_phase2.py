import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from database import init_db, SessionLocal
from models import Fact, Entity
from canonicalizer import canonicalize_fact

def main():
    print("Initializing Database...")
    init_db()
    db = SessionLocal()
    
    facts = db.query(Fact).all()
    print(f"Found {len(facts)} facts to canonicalize.")
    
    for fact in facts:
        canonicalize_fact(db, fact)
        
    print("\n--- Canonicalization Results ---")
    for fact in db.query(Fact).all():
        entity = db.query(Entity).filter(Entity.id == fact.subject_entity_id).first()
        ent_name = entity.canonical_name if entity else "None"
        print(f"Fact ID: {fact.id}")
        print(f"  Entity: {fact.subject} -> Resolved to: {ent_name}")
        print(f"  Predicate: {fact.predicate}")
        print(f"  Value: {fact.raw_value} -> Canonical: {fact.canonical_value} {fact.canonical_unit}")
        print(f"  Time: {fact.time_raw} -> Start: {fact.time_start}, End: {fact.time_end}")
        print("-" * 30)

    db.close()
    print("Phase 2 Complete.")

if __name__ == "__main__":
    main()
