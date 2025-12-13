from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User, UserRole

def get_actor(
    db: Session = Depends(get_db),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> User:
    # Временная логика:
    # если X-Role: ADMIN -> берём admin@shurale.local
    # иначе -> manager@shurale.local
    if x_role == "ADMIN":
        email = "admin@shurale.local"
    else:
        email = "manager@shurale.local"

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=500,
            detail=f"Seed users not found. Run: python -m app.seed (missing {email})",
        )
    return user

def require_admin_role(
    actor: User = Depends(get_actor),
) -> User:
    if actor.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only (set header X-Role: ADMIN)")
    return actor
