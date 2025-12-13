import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ExpenseOut(BaseModel):
    id: uuid.UUID
    amount_cents: int
    payment_source: str  # CASH|CARD|BANK
    category_id: uuid.UUID
    comment: str | None = None
    spent_at: datetime
    receipt_path: str | None = None
    is_deleted: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

class ExpenseCreate(BaseModel):
    amount_cents: int = Field(gt=0)
    payment_source: str  # CASH|CARD|BANK
    category_id: uuid.UUID
    comment: str | None = Field(default=None, max_length=500)
    spent_at: datetime | None = None  # если не передали — возьмём now()

class ExpenseUpdate(BaseModel):
    amount_cents: int | None = Field(default=None, gt=0)
    payment_source: str | None = None
    category_id: uuid.UUID | None = None
    comment: str | None = Field(default=None, max_length=500)
    spent_at: datetime | None = None
