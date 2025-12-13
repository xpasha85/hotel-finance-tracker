import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.admin_guard import require_admin
from app.models.category import Category
from app.schemas.category import CategoryOut, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("", response_model=list[CategoryOut])
def list_categories(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    q = db.query(Category)
    if active_only:
        q = q.filter(Category.is_active == True)  # noqa: E712
    # Сортировка: сначала родители, потом дети, потом по имени
    rows = q.order_by(Category.parent_id.nullsfirst(), Category.name.asc()).all()
    return rows

@router.post("", response_model=CategoryOut)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    # Проверка parent_id (если задан)
    if payload.parent_id:
        parent = db.query(Category).filter(Category.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        # На MVP: родитель должен быть активным
        if not parent.is_active:
            raise HTTPException(status_code=400, detail="Parent category is archived")

    # Уникальность по name (простая, как в модели)
    exists = db.query(Category).filter(Category.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Category name already exists")

    cat = Category(name=payload.name, parent_id=payload.parent_id, is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.name is not None:
        exists = db.query(Category).filter(Category.name == payload.name, Category.id != category_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="Category name already exists")
        cat.name = payload.name

    if payload.parent_id is not None:
        if payload.parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be parent of itself")
        if payload.parent_id:
            parent = db.query(Category).filter(Category.id == payload.parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent category not found")
            if not parent.is_active:
                raise HTTPException(status_code=400, detail="Parent category is archived")
        cat.parent_id = payload.parent_id

    db.commit()
    db.refresh(cat)
    return cat

@router.post("/{category_id}/archive", response_model=CategoryOut)
def archive_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    cat.is_active = False
    db.commit()
    db.refresh(cat)
    return cat

@router.post("/{category_id}/restore", response_model=CategoryOut)
def restore_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    cat.is_active = True
    db.commit()
    db.refresh(cat)
    return cat
