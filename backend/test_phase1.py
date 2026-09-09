import asyncio
from parser import parse_pdf
from extractor import extract_facts, verify_evidence
from database import init_db, SessionLocal
from models import Document, Chunk, Fact
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Initializing Database...")
    init_db()
    
    pdf_path = "test_macro.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: Need a test PDF at {pdf_path}")
        return
        
    print("Parsing PDF...")
    chunks = parse_pdf(pdf_path)
    print(f"Extracted {len(chunks)} chunks.")
    
    if not chunks:
        print("No text found.")
        return
        
    db = SessionLocal()
    
    doc = Document(
        title="Test Document",
        filename="test_macro.pdf",
        storage_path=pdf_path,
        status="extracting",
        page_count=len(chunks),
        doc_type_hint="financial_report"
    )
    db.add(doc)
    db.commit()
    
    print("Running Extraction on first chunk...")
    for chunk_data in chunks[:1]:
        db_chunk = Chunk(
            document_id=doc.id,
            page_number=chunk_data["page_number"],
            text=chunk_data["text"],
            bbox=chunk_data["bboxes"],
            extraction_method="text"
        )
        db.add(db_chunk)
        db.commit()
        
        print(f"\n--- Extracting facts from Page {chunk_data['page_number']} ---")
        try:
            extraction = extract_facts(chunk_data["text"], chunk_data["page_number"], "financial_report")
            
            facts = extraction.get("facts", [])
            print(f"Gemini extracted {len(facts)} facts.")
            for fact_data in facts:
                # Verify Evidence
                is_verified = verify_evidence(fact_data["evidence_text"], chunk_data["text"])
                status = "verified" if is_verified else "unverified"
                
                print(f"Extracted Fact: {fact_data['predicate']} = {fact_data['raw_value']} (Status: {status})")
                print(f"Evidence: {fact_data['evidence_text']}")
                
                time_ctx = fact_data["time_context"]
                scope_ctx = fact_data["scope"]
                db_fact = Fact(
                    document_id=doc.id,
                    chunk_id=db_chunk.id,
                    subject=fact_data["subject"],
                    predicate=fact_data["predicate"],
                    object=fact_data.get("object"),
                    raw_value=fact_data["raw_value"],
                    value_type=fact_data["value_type"],
                    time_period_type=time_ctx.get("period_type"),
                    time_raw=time_ctx.get("raw"),
                    scope_consolidation=scope_ctx.get("consolidation"),
                    scope_segment=scope_ctx.get("segment"),
                    page_number=chunk_data["page_number"],
                    evidence_text=fact_data["evidence_text"],
                    confidence_score=fact_data["confidence_score"],
                    status=status
                )
                db.add(db_fact)
            db.commit()
        except Exception as e:
            print(f"Extraction failed: {e}")

    doc.status = "complete"
    db.commit()
    print("\nPhase 1 Complete.")

if __name__ == "__main__":
    main()
