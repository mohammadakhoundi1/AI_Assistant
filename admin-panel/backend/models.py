from sqlalchemy import Column, Integer, String, Boolean, DateTime ,Text
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin, teacher, student
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LLMSettings(Base):
    __tablename__ = "llm_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class RAGDocument(Base):
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, nullable=False, index=True)  # شماره گروه (مثلاً 7)
    filename = Column(String, nullable=False)  # نام فایل اصلی
    file_type = Column(String, nullable=False)  # pdf, txt, docx
    content = Column(Text, nullable=True)  # محتوای استخراج شده (اختیاری)
    chunk_count = Column(Integer, default=0)  # تعداد chunk های ایجاد شده
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
