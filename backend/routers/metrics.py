from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import PDFDocument
from datetime import datetime
from schemas import DashboardMetricsSchema



router = APIRouter(prefix="/metrics")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=DashboardMetricsSchema)
def metrics(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(PDFDocument)

    if start_date:
        # Parse the date string and compare only the date part
        start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
        query = query.filter(
            func.date(PDFDocument.uploaded_at) >= start_date_obj
        )

    if end_date:
        # Parse the date string and compare only the date part
        end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
        query = query.filter(
            func.date(PDFDocument.uploaded_at) <= end_date_obj
        )
    total = query.count()
    processed = query.filter(PDFDocument.status == "completed").count()
    failed = query.filter(PDFDocument.status == "failed").count()

    daily = (
        query.with_entities(
            func.date(PDFDocument.uploaded_at).label("date"),
            func.count().label("count")
        )
        .group_by(func.date(PDFDocument.uploaded_at))
        .order_by(func.date(PDFDocument.uploaded_at))
        .all()
    )

    return {
        "total": total,
        "processed": processed,
        "failed": failed,
        "daily_uploads": [
            {"date": str(d.date), "count": d.count} for d in daily
        ]
    }
