from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.category import Category

# def ensure_tables():
#     # на старте можно так, но в норме будем через alembic
#     Base.metadata.create_all(bind=engine)

def seed_min(db: Session):
    # users
    admin_email = "admin@local"
    manager_email = "manager@local"

    if not db.query(User).filter(User.email == admin_email).first():
        db.add(User(email=admin_email, password_hash=bcrypt.hash("admin"), role=UserRole.ADMIN))
    if not db.query(User).filter(User.email == manager_email).first():
        db.add(User(email=manager_email, password_hash=bcrypt.hash("manager"), role=UserRole.MANAGER))

    # categories
    base = ["Продукты", "Хозтовары", "Ремонт", "Зарплаты", "Маркетинг", "Коммуналка", "Прочее"]
    for name in base:
        if not db.query(Category).filter(Category.name == name).first():
            db.add(Category(name=name, is_active=True))

    db.commit()

def main():
    ensure_tables()
    db = SessionLocal()
    try:
        seed_min(db)
        print("Seed done: users=2, categories=7")
        print("Login: admin@local / admin")
        print("Login: manager@local / manager")
    finally:
        db.close()

if __name__ == "__main__":
    main()
