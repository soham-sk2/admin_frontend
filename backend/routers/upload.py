from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from database import SessionLocal
from models import PDFDocument
from services.pdf_pipeline import process_pdf
from auth.deps import get_current_admin
from schemas import UploadResponseSchema, RetryResponseSchema

router = APIRouter(prefix="/upload")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=UploadResponseSchema)
async def upload_pdf(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    # ✅ Check if file with same name is already processed
    existing = db.query(PDFDocument).filter(
        PDFDocument.filename == file.filename,
        PDFDocument.status == "completed"
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="File already processed successfully"
        )
    
    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{file.filename}"

    with open(path, "wb") as f:
        f.write(await file.read())

    pdf = PDFDocument(
        filename=file.filename,
        size=os.path.getsize(path),
        status="uploaded",
        uploaded_by_email=admin.email
    )

    db.add(pdf)
    db.commit()
    db.refresh(pdf)

    background_tasks.add_task(process_pdf, pdf.id)

    return {
        "id": pdf.id,
        "filename": pdf.filename,
        "status": pdf.status,
        "message": "File uploaded and processing started"
    }

@router.post("/retry/{pdf_id}", response_model=RetryResponseSchema)
async def retry_processing(
    pdf_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Retry processing for failed or stuck uploads"""
    pdf = db.query(PDFDocument).filter(PDFDocument.id == pdf_id).first()
    
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    if pdf.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="File already processed successfully"
        )
    
    if pdf.status == "processing":
        raise HTTPException(
            status_code=400,
            detail="File is currently being processed"
        )
    
    # Reset status to uploaded and retry
    pdf.status = "uploaded"
    db.commit()
    
    background_tasks.add_task(process_pdf, pdf.id)
    
    return {
        "id": pdf.id,
        "filename": pdf.filename,
        "status": "retry_started",
        "message": "Processing retry initiated"
    }