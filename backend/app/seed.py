import bcrypt
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.user import User, UserRole

def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def run():
    db: Session = SessionLocal()
    try:
        admin_email = "admin@shurale.local"
        manager_email = "manager@shurale.local"

        if not db.query(User).filter(User.email == admin_email).first():
            db.add(User(email=admin_email, password_hash=_hash("admin"), role=UserRole.ADMIN))

        if not db.query(User).filter(User.email == manager_email).first():
            db.add(User(email=manager_email, password_hash=_hash("manager"), role=UserRole.MANAGER))

        db.commit()
        print("Seed OK: admin + manager created (if absent).")
    finally:
        db.close()

if __name__ == "__main__":
    run()
