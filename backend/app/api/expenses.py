import uuid
from datetime import datetime, date, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.actor import get_actor, require_admin_role
from app.models.expense import Expense
from app.models.expense_history import ExpenseHistory
from app.models.category import Category
from app.models.user import User
from app.schemas.expense import ExpenseOut, ExpenseCreate, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["expenses"])

ALLOWED_SOURCES = {"CASH", "CARD", "BANK"}

def _dt_start(d: date) -> datetime:
    return datetime.combine(d, time.min)

def _dt_end(d: date) -> datetime:
    return datetime.combine(d, time.max)

def _make_diff(old: Expense, new_data: dict) -> dict:
    diff = {}
    for k, new_v in new_data.items():
        old_v = getattr(old, k)
        if old_v != new_v:
            diff[k] = {"old": old_v, "new": new_v}
    return diff

def _write_history(db: Session, expense_id: uuid.UUID, action: str, diff: dict, actor_id: uuid.UUID) -> None:
    h = ExpenseHistory(
        expense_id=expense_id,
        action=action,
        diff_json=diff or {},
        actor_id=actor_id,
    )
    db.add(h)

@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category_ids: list[uuid.UUID] | None = Query(default=None),
    payment_source: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    db: Session = Depends(get_db),
    actor: User = Depends(get_actor),
):
    q = db.query(Expense)

    # По умолчанию менеджер НЕ видит удалённые.
    # Админ может включить include_deleted=true
    if include_deleted:
        if actor.role != actor.role.ADMIN:  # type: ignore[attr-defined]
            # на всякий — но лучше через require_admin_role, оставлю в явном виде:
            raise HTTPException(status_code=403, detail="Admin only for include_deleted")
    else:
        q = q.filter(Expense.is_deleted == False)  # noqa: E712

    if date_from:
        q = q.filter(Expense.spent_at >= _dt_start(date_from))
    if date_to:
        q = q.filter(Expense.spent_at <= _dt_end(date_to))

    if category_ids:
        q = q.filter(Expense.category_id.in_(category_ids))

    if payment_source:
        ps = payment_source.upper()
        if ps not in ALLOWED_SOURCES:
            raise HTTPException(status_code=400, detail="payment_source must be CASH|CARD|BANK")
        q = q.filter(Expense.payment_source == ps)

    return q.order_by(Expense.spent_at.desc()).all()

@router.post("", response_model=ExpenseOut)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_actor),
):
    ps = payload.payment_source.upper()
    if ps not in ALLOWED_SOURCES:
        raise HTTPException(status_code=400, detail="payment_source must be CASH|CARD|BANK")

    cat = db.query(Category).filter(Category.id == payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if not cat.is_active:
        raise HTTPException(status_code=400, detail="Category is archived")

    exp = Expense(
        amount_cents=payload.amount_cents,
        payment_source=ps,
        category_id=payload.category_id,
        comment=payload.comment,
        spent_at=payload.spent_at or datetime.utcnow(),
        receipt_path=None,
        is_deleted=False,
        deleted_at=None,
        deleted_by=None,
        created_by=actor.id,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    _write_history(db, exp.id, "CREATE", {"created": True}, actor.id)
    db.commit()

    return exp

@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_actor),
):
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    if exp.is_deleted and actor.role != actor.role.ADMIN:  # type: ignore[attr-defined]
        raise HTTPException(status_code=403, detail="Cannot edit deleted expense (admin only)")

    update_data = {}

    if payload.amount_cents is not None:
        update_data["amount_cents"] = payload.amount_cents

    if payload.payment_source is not None:
        ps = payload.payment_source.upper()
        if ps not in ALLOWED_SOURCES:
            raise HTTPException(status_code=400, detail="payment_source must be CASH|CARD|BANK")
        update_data["payment_source"] = ps

    if payload.category_id is not None:
        cat = db.query(Category).filter(Category.id == payload.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        if not cat.is_active:
            raise HTTPException(status_code=400, detail="Category is archived")
        update_data["category_id"] = payload.category_id

    if payload.comment is not None:
        update_data["comment"] = payload.comment

    if payload.spent_at is not None:
        update_data["spent_at"] = payload.spent_at

    diff = _make_diff(exp, update_data)

    for k, v in update_data.items():
        setattr(exp, k, v)

    db.commit()
    db.refresh(exp)

    if diff:
        _write_history(db, exp.id, "UPDATE", diff, actor.id)
        db.commit()

    return exp

@router.post("/{expense_id}/delete", response_model=ExpenseOut)
def soft_delete_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_actor),
):
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    if not exp.is_deleted:
        exp.is_deleted = True
        exp.deleted_at = datetime.utcnow()
        exp.deleted_by = actor.id
        db.commit()
        db.refresh(exp)

        _write_history(db, exp.id, "DELETE", {"is_deleted": {"old": False, "new": True}}, actor.id)
        db.commit()

    return exp

@router.post("/{expense_id}/restore", response_model=ExpenseOut)
def restore_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_role),
):
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    if exp.is_deleted:
        exp.is_deleted = False
        exp.deleted_at = None
        exp.deleted_by = None
        db.commit()
        db.refresh(exp)

        _write_history(db, exp.id, "RESTORE", {"is_deleted": {"old": True, "new": False}}, admin.id)
        db.commit()

    return exp

@router.get("/{expense_id}/history")
def get_expense_history(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin_role),
):
    rows = (
        db.query(ExpenseHistory)
        .filter(ExpenseHistory.expense_id == expense_id)
        .order_by(ExpenseHistory.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "action": r.action,
            "diff_json": r.diff_json,
            "actor_id": str(r.actor_id),
            "created_at": r.created_at,
        }
        for r in rows
    ]
