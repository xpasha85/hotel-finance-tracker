import os
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.actor import get_actor
from app.models.expense import Expense
from app.models.user import User, UserRole

router = APIRouter(prefix="/expenses", tags=["receipts"])

def _receipts_dir() -> Path:
  p = Path(os.getenv("RECEIPTS_DIR", "/data/receipts"))
  p.mkdir(parents=True, exist_ok=True)
  return p

@router.post("/{expense_id}/receipt")
async def upload_receipt(
    expense_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(get_actor),
):
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Менеджеру можно загружать чек только к НЕудалённой записи
    if exp.is_deleted and actor.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot attach receipt to deleted expense (admin only)")

    # грубая валидация типа
    ct = (file.content_type or "").lower()
    if not (ct.startswith("image/") or ct == "application/pdf"):
        raise HTTPException(status_code=400, detail="Only images or PDF allowed")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".pdf"]:
        # если расширение странное — подставим по content-type
        ext = ".pdf" if ct == "application/pdf" else ".jpg"

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"{expense_id}_{ts}_{uuid.uuid4().hex}{ext}"
    out_path = _receipts_dir() / name

    # сохранить файл
    with out_path.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    # сохранить относительный путь (чтобы на VPS было переносимо)
    exp.receipt_path = name
    db.commit()
    db.refresh(exp)

    return {
        "expense_id": str(expense_id),
        "receipt_path": name,
        "url": f"/receipts/{name}",
    }
