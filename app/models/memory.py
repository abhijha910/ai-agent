"""
Memory and Knowledge Base models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    key = Column(String(255), index=True)  # Memory key/topic
    value = Column(Text)  # Memory content
    importance = Column(Float, default=0.5)  # 0.0 to 1.0
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default={})


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255))
    content = Column(Text)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)  # pdf, docx, txt, etc.
    embedding = Column(JSON, nullable=True)  # Vector embedding
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default={})

