import uuid
from datetime import datetime
from pydantic import BaseModel

class ExpenseHistoryOut(BaseModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    action: str
    diff_json: dict
    actor_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
