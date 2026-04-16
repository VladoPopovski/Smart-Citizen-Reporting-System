from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.report import Report
from app.models.category import Category


def get_summary(db: Session):
    # 📊 1. Reports per category
    reports_per_category = (
        db.query(Category.name, func.count(Report.id))
        .join(Report, Report.category_id == Category.id)
        .group_by(Category.name)
        .all()
    )

    reports_per_category_result = [
        {"category": name, "count": count}
        for name, count in reports_per_category
    ]

    # 📊 2. Resolved / Unresolved
    resolved_status_id = 2
    unresolved_status_id = 1

    resolved = db.query(func.count(Report.id)).filter(
        Report.status_id == resolved_status_id
    ).scalar()

    unresolved = db.query(func.count(Report.id)).filter(
        Report.status_id == unresolved_status_id
    ).scalar()

    # 📊 3. Trend by month
    trend_data = (
        db.query(
            func.date_trunc('month', Report.created_at),
            func.count(Report.id)
        )
        .group_by(func.date_trunc('month', Report.created_at))
        .order_by(func.date_trunc('month', Report.created_at))
        .all()
    )

    trend_result = [
        {"month": str(month), "count": count}
        for month, count in trend_data
    ]

    return {
        "reports_per_category": reports_per_category_result,
        "resolved": resolved,
        "unresolved": unresolved,
        "trend": trend_result
    }