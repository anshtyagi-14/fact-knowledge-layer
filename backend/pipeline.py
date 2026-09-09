import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Document, ProcessingJob, Chunk, Fact
from parser import parse_pdf
from extractor import extract_facts, verify_evidence
from canonicalizer import canonicalize_fact
from matcher import embed_fact, find_candidate_pairs
from classifier import classify_relationship

def process_document(document_id, job_id):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        
        # Stage: Parsing
        job.stage = "parsing"
        job.status = "in_progress"
        doc.status = "parsing"
        db.commit()
        
        chunks_data = parse_pdf(doc.storage_path)
        doc.page_count = len(chunks_data)
        
        db_chunks = []
        for c_data in chunks_data:
            chunk = Chunk(
                document_id=doc.id,
                page_number=c_data["page_number"],
                text=c_data["text"],
                bbox=c_data["bboxes"],
                extraction_method="text"
            )
            db.add(chunk)
            db_chunks.append((chunk, c_data))
        db.commit()
        
        # Stage: Extracting
        job.stage = "extracting"
        doc.status = "extracting"
        db.commit()
        
        for chunk, c_data in db_chunks:
            # simple mock delay to prevent rate limits on free tier
            time.sleep(2)
            try:
                extraction = extract_facts(c_data["text"], c_data["page_number"], "financial_report")
                facts = extraction.get("facts", [])
                
                for f_data in facts:
                    is_verified = verify_evidence(f_data["evidence_text"], c_data["text"])
                    
                    from test_mapping import find_best_bbox
                    best_bbox = find_best_bbox(f_data["evidence_text"], c_data["bboxes"])
                    f_data["evidence_bbox"] = best_bbox

                    status = "verified" if is_verified else "unverified"
                    
                    time_ctx = f_data["time_context"]
                    scope_ctx = f_data["scope"]
                    
                    fact = Fact(
                        document_id=doc.id,
                        chunk_id=chunk.id,
                        subject=f_data["subject"],
                        predicate=f_data["predicate"],
                        object=f_data.get("object"),
                        raw_value=f_data["raw_value"],
                        value_type=f_data["value_type"],
                        time_period_type=time_ctx.get("period_type"),
                        time_raw=time_ctx.get("raw"),
                        scope_consolidation=scope_ctx.get("consolidation"),
                        scope_segment=scope_ctx.get("segment"),
                        page_number=c_data["page_number"],
                        evidence_text=f_data["evidence_text"],
                        confidence_score=f_data["confidence_score"],
                        status=status
                    )
                    db.add(fact)
                db.commit()
            except Exception as e:
                print(f"Extraction error: {e}")
                
        # Stage: Canonicalizing
        job.stage = "canonicalizing"
        db.commit()
        
        doc_facts = db.query(Fact).filter(Fact.document_id == doc.id).all()
        for fact in doc_facts:
            canonicalize_fact(db, fact)
            time.sleep(1) # rate limit protection
            
        # Stage: Matching
        job.stage = "matching"
        doc.status = "matching"
        db.commit()
        
        for fact in doc_facts:
            embed_fact(db, fact)
            time.sleep(1)
            
        # Stage: Classifying
        job.stage = "classifying"
        doc.status = "classifying"
        db.commit()
        
        for fact in doc_facts:
            candidates = find_candidate_pairs(db, fact, threshold=0.85)
            for candidate in candidates:
                if fact.id < candidate.id:
                    classify_relationship(db, fact, candidate)
                    time.sleep(2) # rate limit protection
                    
        job.stage = "complete"
        job.status = "complete"
        doc.status = "complete"
        db.commit()
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        doc.status = "failed"
        db.commit()
        print(f"Job Failed: {e}")
    finally:
        db.close()
