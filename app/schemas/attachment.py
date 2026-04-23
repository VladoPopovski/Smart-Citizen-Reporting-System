from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    file_url: str
    created_at: datetime