from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    old_status_id: int | None = None
    status_id: int | None = None
    created_at: datetime