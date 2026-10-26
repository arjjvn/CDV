from getpass import getpass

from argon2 import PasswordHasher
from sqlalchemy.orm import Session

from Backend import models
from Backend.database import SessionLocal, create_tables
from Backend.models import User


def create_admin():
    create_tables()

    email = input("Admin email: ").strip().lower()
    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()

    password = getpass("Create password (minimum 8 characters): ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db: Session = SessionLocal()

    try:
        existing = db.query(User).filter(
            User.email == email
        ).first()

        if existing:
            print("An account with this email already exists.")
            return

        admin = User(
            username=email.split("@")[0][:50],
            email=email,
            hashed_password=PasswordHasher().hash(password),
            role="admin",
            is_approved=True,
            first_name=first_name,
            last_name=last_name,
        )

        db.add(admin)
        db.commit()

        print("Admin account created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()