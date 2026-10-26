
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from Backend.database_dependency import get_db
from Backend.models import Volunteer

router = APIRouter(prefix="/volunteers", tags=["Volunteers"])


class VolunteerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    skills: list[str] = Field(min_length=1)
    location: str = Field(min_length=1, max_length=100)


@router.post("/register", status_code=201)
def register_volunteer(
    volunteer: VolunteerCreate,
    db: Session = Depends(get_db),
):
    normalized_email = str(volunteer.email).lower()

    existing_volunteer = (
        db.query(Volunteer)
        .filter(Volunteer.email.ilike(normalized_email))
        .first()
    )

    if existing_volunteer:
        raise HTTPException(
            status_code=409,
            detail="A volunteer with this email already exists",
        )

    new_volunteer = Volunteer(
        name=volunteer.name,
        email=normalized_email,
        skills=volunteer.skills,
        location=volunteer.location,
    )

    db.add(new_volunteer)

    try:
        db.commit()
        db.refresh(new_volunteer)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Volunteer registered successfully",
        "volunteer": {
            "id": new_volunteer.id,
            "name": new_volunteer.name,
            "email": new_volunteer.email,
            "skills": new_volunteer.skills,
            "location": new_volunteer.location,
        },
    }

@router.get("/")
def list_volunteers(db: Session = Depends(get_db)):
    volunteers = db.query(Volunteer).order_by(Volunteer.id).all()

    return [
        {
            "id": volunteer.id,
            "name": volunteer.name,
            "email": volunteer.email,
            "skills": volunteer.skills,
            "location": volunteer.location,
        }
        for volunteer in volunteers
    ]
