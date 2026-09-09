from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid
import shutil
import os
import pymupdf

from database import get_db, init_db
from models import Document, Fact, FactRelationship, ProcessingJob, Entity
from pipeline import process_document

app = FastAPI(title="Fact Knowledge Layer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/documents")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    doc = Document(title=file.filename, filename=file.filename, storage_path=file_path, status="uploaded", page_count=0)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    job = ProcessingJob(document_id=doc.id, stage="uploaded", status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(process_document, doc.id, job.id)
    return {"document_id": str(doc.id), "job_id": str(job.id), "status": "queued"}

@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()

@app.get("/documents/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.id == doc_id).first()

@app.get("/documents/{doc_id}/pages/{page_num}/image")
def get_page_image(doc_id: str, page_num: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return {"error": "Not found"}
    pdf_doc = pymupdf.open(doc.storage_path)
    page = pdf_doc.load_page(page_num - 1)
    pix = page.get_pixmap(dpi=150)
    return Response(content=pix.tobytes("png"), media_type="image/png")

def format_fact(f, ent, doc=None):
    return {
        "id": str(f.id),
        "predicate": f.predicate,
        "raw_value": f.raw_value,
        "canonical_value": float(f.canonical_value) if f.canonical_value else None,
        "canonical_unit": f.canonical_unit,
        "time_raw": f.time_raw,
        "scope_segment": f.scope_segment,
        "evidence_text": f.evidence_text,
        "evidence_bbox": f.evidence_bbox,
        "page_number": f.page_number,
        "status": f.status,
        "subject": ent.canonical_name if ent else f.subject,
        "document_id": str(f.document_id),
        "document_title": doc.title if doc else None
    }

@app.get("/documents/{doc_id}/facts")
def get_document_facts(doc_id: str, db: Session = Depends(get_db)):
    facts = db.query(Fact).filter(Fact.document_id == doc_id).all()
    return [format_fact(f, db.query(Entity).filter(Entity.id == f.subject_entity_id).first()) for f in facts]

@app.get("/facts")
def list_facts(document_id: str = None, predicate: str = None, db: Session = Depends(get_db)):
    q = db.query(Fact)
    if document_id:
        q = q.filter(Fact.document_id == document_id)
    if predicate:
        q = q.filter(Fact.predicate.ilike(f"%{predicate}%"))
    facts = q.all()
    res = []
    for f in facts:
        ent = db.query(Entity).filter(Entity.id == f.subject_entity_id).first()
        doc = db.query(Document).filter(Document.id == f.document_id).first()
        res.append(format_fact(f, ent, doc))
    return res

@app.get("/relationships")
def list_relationships(rel_type: str = None, db: Session = Depends(get_db)):
    q = db.query(FactRelationship)
    if rel_type:
        q = q.filter(FactRelationship.relationship_type == rel_type)
    rels = q.all()
    res = []
    for r in rels:
        fa = db.query(Fact).filter(Fact.id == r.fact_a_id).first()
        fb = db.query(Fact).filter(Fact.id == r.fact_b_id).first()
        if not fa or not fb: continue
        
        ent_a = db.query(Entity).filter(Entity.id == fa.subject_entity_id).first()
        ent_b = db.query(Entity).filter(Entity.id == fb.subject_entity_id).first()
        doc_a = db.query(Document).filter(Document.id == fa.document_id).first()
        doc_b = db.query(Document).filter(Document.id == fb.document_id).first()
        
        res.append({
            "id": str(r.id),
            "relationship_type": r.relationship_type,
            "confidence": float(r.confidence) if r.confidence else 0,
            "reasoning": r.reasoning,
            "requires_human_review": r.requires_human_review,
            "fact_a": format_fact(fa, ent_a, doc_a),
            "fact_b": format_fact(fb, ent_b, doc_b)
        })
    return res

@app.get("/stats")
def get_summary_stats(db: Session = Depends(get_db)):
    return {
        "total_documents": db.query(Document).count(),
        "total_facts": db.query(Fact).count(),
        "unverified_facts": db.query(Fact).filter(Fact.status == "unverified").count(),
        "relationships": {
            "CORROBORATES": db.query(FactRelationship).filter(FactRelationship.relationship_type == "CORROBORATES").count(),
            "CONTRADICTS": db.query(FactRelationship).filter(FactRelationship.relationship_type == "CONTRADICTS").count(),
            "RECONCILED": db.query(FactRelationship).filter(FactRelationship.relationship_type == "RECONCILED").count(),
            "NEW_FACT": db.query(FactRelationship).filter(FactRelationship.relationship_type == "NEW_FACT").count()
        }
    }
