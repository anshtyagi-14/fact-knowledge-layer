from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Numeric, Date, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector
from database import Base
import uuid
import datetime

class Document(Base):
    __tablename__ = 'documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    filename = Column(String)
    storage_path = Column(String)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = Column(String) 
    page_count = Column(Integer)
    doc_type_hint = Column(String)
    metadata_ = Column("metadata", JSON)

class Chunk(Base):
    __tablename__ = 'chunks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    page_number = Column(Integer)
    text = Column(Text)
    bbox = Column(JSON)
    extraction_method = Column(String)
    embedding = Column(Vector(3072))

class Entity(Base):
    __tablename__ = 'entities'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name = Column(String)
    entity_type = Column(String)
    aliases = Column(ARRAY(String))
    metadata_ = Column("metadata", JSON)

class Fact(Base):
    __tablename__ = 'facts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    chunk_id = Column(UUID(as_uuid=True), ForeignKey('chunks.id'))
    subject_entity_id = Column(UUID(as_uuid=True), ForeignKey('entities.id'), nullable=True)
    subject = Column(String) # Raw subject string before resolution
    predicate = Column(String)
    object = Column(String, nullable=True)
    raw_value = Column(String)
    canonical_value = Column(Numeric, nullable=True)
    canonical_unit = Column(String, nullable=True)
    value_type = Column(String)
    time_period_type = Column(String, nullable=True)
    time_start = Column(Date, nullable=True)
    time_end = Column(Date, nullable=True)
    time_raw = Column(String, nullable=True)
    scope_consolidation = Column(String, nullable=True)
    scope_segment = Column(String, nullable=True)
    page_number = Column(Integer)
    evidence_text = Column(Text)
    evidence_bbox = Column(JSON, nullable=True)
    extraction_method = Column(String)
    confidence_score = Column(Numeric)
    status = Column(String) 
    embedding = Column(Vector(3072), nullable=True)
    extracted_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class FactRelationship(Base):
    __tablename__ = 'fact_relationships'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fact_a_id = Column(UUID(as_uuid=True), ForeignKey('facts.id'))
    fact_b_id = Column(UUID(as_uuid=True), ForeignKey('facts.id'))
    relationship_type = Column(String) 
    confidence = Column(Numeric)
    reasoning = Column(Text)
    classification_method = Column(String) 
    requires_human_review = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class ProcessingJob(Base):
    __tablename__ = 'processing_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    stage = Column(String)
    status = Column(String)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
