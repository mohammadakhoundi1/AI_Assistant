from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, UploadFile, File
from chat.websocket import chat_websocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from typing import List, Dict
from database import engine, get_db, Base
from models import User, LLMSettings, RAGDocument  # ✅ اضافه کردن RAGDocument
from schemas import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    LoginRequest,
    LLMSettingsUpdate,
    ModelsFetchRequest,
    ModelInfo,
    ModelsListResponse
)
import httpx
import os
from pathlib import Path

# ✅ Import RAG System
from rag import RAGSystem

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Admin Panel API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ✅ دیکشنری نگهداری RAG Systems (هر گروه یک سیستم مجزا)
rag_systems: Dict[int, RAGSystem] = {}

# ✅ مسیر ذخیره فایل‌های آپلود شده
UPLOAD_DIR = Path("backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure current user is an admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# ✅ تابع بارگذاری RAG Systems در Startup
@app.on_event("startup")
async def load_rag_systems():
    """بارگذاری خودکار RAG Systems برای تمام گروه‌ها"""
    db = next(get_db())
    try:
        # دریافت تنظیمات LLM
        llm_settings = db.query(LLMSettings).first()
        if not llm_settings:
            print("⚠️ No LLM settings found - RAG systems will not be initialized")
            return
        
        api_key = llm_settings.api_key
        
        # دریافت لیست گروه‌های موجود
        groups = db.query(RAGDocument.group_id).distinct().all()
        
        for (group_id,) in groups:
            try:
                print(f"\n🔄 Loading RAG system for Group {group_id}...")
                rag_system = RAGSystem(group_id=group_id, api_key=api_key)
                
                # بارگذاری ChromaDB
                if rag_system.load_existing():
                    rag_systems[group_id] = rag_system
                    doc_count = db.query(RAGDocument).filter(
                        RAGDocument.group_id == group_id
                    ).count()
                    print(f"✅ RAG system loaded for Group {group_id} ({doc_count} documents)")
                else:
                    print(f"⚠️ No ChromaDB found for Group {group_id}")
            except Exception as e:
                print(f"❌ Failed to load RAG system for Group {group_id}: {e}")
        
        print(f"\n✅ Total RAG systems loaded: {len(rag_systems)}")
    finally:
        db.close()

# Authentication Endpoints
@app.get("/")
def read_root():
    return {"message": "Admin Panel API is running"}

@app.websocket("/ws/chat/{role}")
async def ws_chat(websocket: WebSocket, role: str, db: Session = Depends(get_db)):
    # دریافت تنظیمات از دیتابیس
    settings = db.query(LLMSettings).first()
    
    if settings:
        llm_settings = {
            "api_key": settings.api_key,
            "base_url": settings.base_url,
            "model_name": settings.model_name
        }
        print(f"\n🔌 WebSocket connected - Role: {role}")
        print(f"📥 LLM Settings from DB:")
        print(f"   Base URL: {llm_settings['base_url']}")
        print(f"   Model: {llm_settings['model_name']}")
        print(f"   API Key Length: {len(llm_settings['api_key'])} chars\n")
    else:
        llm_settings = {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": ""
        }
        print(f"\n⚠️ WebSocket connected but NO LLM settings found in DB")
        print(f"   Using default/empty settings\n")
    
    # ✅ ارسال RAG Systems به WebSocket
    await chat_websocket(websocket, role, llm_settings, rag_systems)

@app.post("/auth/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_count = db.query(User).count()
    hashed_password = get_password_hash(user.password)
    
    if user_count == 0:
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role="admin",
            is_approved=True
        )
    else:
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role, 
            is_approved=False
        )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "is_approved": user.is_approved
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

# CRUD Endpoints (Admin Only)

@app.get("/admin/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (Admin only)"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@app.get("/admin/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get specific user by ID (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/admin/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user information (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id and user_update.role != "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot change your role - you are the last admin"
            )
    
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.is_approved is not None:
        user.is_approved = user_update.is_approved
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    return user

@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user (Admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last admin user"
            )
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully", "deleted_user_id": user_id}

@app.get("/admin/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user), 
    db: Session = Depends(get_db)
):
    total = db.query(User).count()
    admins = db.query(User).filter(User.role == "admin").count()
    teachers = db.query(User).filter(User.role == "teacher").count()
    students = db.query(User).filter(User.role == "student").count()
    pending = db.query(User).filter(User.is_approved == False).count()
    
    return {
        "total": total,
        "admins": admins,
        "teachers": teachers,
        "students": students,
        "pending": pending
    }

# LLM Settings Endpoints

@app.get("/admin/llm-settings")
async def get_llm_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get LLM settings from database"""
    print(f"📥 GET LLM Settings - User: {current_user.email}, Role: {current_user.role}")
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = db.query(LLMSettings).first()
    
    if not settings:
        print("⚠️ No LLM settings found in DB, returning defaults")
        return {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": ""
        }
    
    print(f"✅ Returning settings from DB (API Key length: {len(settings.api_key)})")
    return {
        "api_key": settings.api_key,
        "base_url": settings.base_url,
        "model_name": settings.model_name
    }

@app.put("/admin/llm-settings")
async def update_llm_settings(
    update_data: LLMSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update LLM settings in database"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    print("\n" + "="*60)
    print("🔧 UPDATING LLM SETTINGS IN DATABASE")
    print(f"👤 Admin: {current_user.email}")
    print(f"📥 Base URL: {update_data.base_url}")
    print(f"📥 Model: {update_data.model_name}")
    print(f"📥 API Key Length: {len(update_data.api_key)} characters")
    
    settings = db.query(LLMSettings).first()
    
    if not settings:
        print("📝 Creating NEW LLM settings record...")
        settings = LLMSettings(
            api_key=update_data.api_key,
            base_url=update_data.base_url,
            model_name=update_data.model_name
        )
        db.add(settings)
    else:
        print("✏️ Updating EXISTING LLM settings...")
        settings.api_key = update_data.api_key
        settings.base_url = update_data.base_url
        settings.model_name = update_data.model_name
    
    db.commit()
    db.refresh(settings)
    
    print("✅ Settings SAVED to database successfully")
    print("="*60 + "\n")
    
    return {
        "message": "Settings updated successfully",
        "settings": {
            "api_key": settings.api_key,
            "base_url": settings.base_url,
            "model_name": settings.model_name
        }
    }

@app.post("/admin/llm-settings/models", response_model=ModelsListResponse)
async def fetch_available_models(
    request: ModelsFetchRequest,
    current_user: User = Depends(get_current_user)
):
    """Fetch available models from LLM provider"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        print(f"[DEBUG] Fetching models from: {request.base_url}")
        print(f"[DEBUG] Using API key: {request.api_key[:10]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{request.base_url}/models",
                headers={"Authorization": f"Bearer {request.api_key}"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[DEBUG] Raw response keys: {data.keys()}")
            
            models = [
                ModelInfo(
                    model_id=model["id"],
                    model_name=model.get("name", model.get("display_name", model["id"]))
                )
                for model in data.get("data", [])
            ]
            
            print(f"[DEBUG] Parsed {len(models)} models")
            if models:
                print(f"[DEBUG] First model: id={models[0].model_id}, name={models[0].model_name}")
            
            return ModelsListResponse(models=models)
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

# ✅ RAG Endpoints

@app.post("/admin/rag/upload/{group_id}")
async def upload_rag_document(
    group_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """آپلود فایل برای RAG - فقط Admin"""
    
    try:
        # بررسی نوع فایل
        allowed_extensions = [".pdf", ".txt", ".docx"]
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"فقط فایل‌های {', '.join(allowed_extensions)} مجاز هستند"
            )
        
        print(f"\n📤 Uploading file for Group {group_id}:")
        print(f"   Filename: {file.filename}")
        print(f"   Type: {file_ext}")
        print(f"   Admin: {current_user.email}")
        
        # ذخیره فایل
        file_path = UPLOAD_DIR / f"group_{group_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # دریافت API Key از دیتابیس
        llm_settings = db.query(LLMSettings).first()
        if not llm_settings:
            raise HTTPException(
                status_code=400,
                detail="ابتدا تنظیمات LLM را در پنل ادمین ثبت کنید"
            )
        
        # ساخت یا بارگذاری RAG System
        if group_id not in rag_systems:
            rag_systems[group_id] = RAGSystem(
                group_id=group_id,
                api_key=llm_settings.api_key,
                base_url=llm_settings.base_url,
                embedding_model="openai/text-embedding-3-small",
            )
        
        rag_system = rag_systems[group_id]
        
        # پردازش فایل و اضافه کردن به ChromaDB
        chunk_count = await rag_system.add_document(str(file_path))
        
        # ذخیره اطلاعات در دیتابیس
        db_document = RAGDocument(
            group_id=group_id,
            filename=file.filename,
            file_type=file_ext[1:],  # بدون نقطه
            chunk_count=chunk_count
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        print(f"✅ File processed successfully:")
        print(f"   Chunks created: {chunk_count}")
        print(f"   Database ID: {db_document.id}")
        
        return {
            "message": "فایل با موفقیت آپلود و پردازش شد",
            "document_id": db_document.id,
            "filename": file.filename,
            "chunk_count": chunk_count,
            "group_id": group_id
        }
        
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/rag/documents/{group_id}")
async def get_rag_documents(
    group_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """دریافت لیست فایل‌های آپلود شده برای یک گروه"""
    
    documents = db.query(RAGDocument).filter(
        RAGDocument.group_id == group_id
    ).order_by(RAGDocument.uploaded_at.desc()).all()
    
    return {
        "group_id": group_id,
        "total_documents": len(documents),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "chunk_count": doc.chunk_count,
                "uploaded_at": doc.uploaded_at.isoformat()
            }
            for doc in documents
        ]
    }

@app.delete("/admin/rag/documents/{document_id}")
async def delete_rag_document(
    document_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """حذف یک سند از RAG"""
    
    document = db.query(RAGDocument).filter(RAGDocument.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="سند یافت نشد")
    
    # حذف از دیتابیس
    db.delete(document)
    db.commit()
    
    # اگر گروه دیگر سندی ندارد، ChromaDB رو پاک کن
    remaining_docs = db.query(RAGDocument).filter(
        RAGDocument.group_id == document.group_id
    ).count()
    
    if remaining_docs == 0 and document.group_id in rag_systems:
        rag_systems[document.group_id].clear()
        del rag_systems[document.group_id]
        print(f"🗑️ Cleared RAG system for Group {document.group_id}")
    
    return {
        "message": "سند با موفقیت حذف شد",
        "document_id": document_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
