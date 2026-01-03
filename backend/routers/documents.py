from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import PDFDocument

router = APIRouter(prefix="/documents")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(PDFDocument)\
                 .order_by(PDFDocument.uploaded_at.desc())\
                 .all()
    
    # Add a 'can_retry' flag for frontend
    result = []
    for doc in documents:
        doc_dict = {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "size": doc.size,
            "uploaded_by_email": doc.uploaded_by_email,
            "uploaded_at": doc.uploaded_at,
            "processed_at": doc.processed_at,
            "can_retry": doc.status in ["failed", "uploaded"]  # Allow retry for failed or stuck uploads
        }
        result.append(doc_dict)
    
    return result