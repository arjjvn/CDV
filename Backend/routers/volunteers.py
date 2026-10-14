from fastapi import APIRouter,HTTPException
from pydantic import BaseModel, Field, EmailStr

router=APIRouter(prefix="/volunteers",tags=["Volunteers"])

class VolunteerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    skills: list[str]=Field(min_length=1)
    location: str=Field(min_length=1,max_length=100)

# Temporary storage for learning; resets when the server restarts
volunteers=[]

@router.post("/register")
def register_volunteer(volunteer:VolunteerCreate):
    for existing_volunteer in volunteers:
        if existing_volunteer['email'].lower()==str(volunteer.email).lower():
            raise HTTPException(
                status_code=409,
                detail="A volunteer with this email already exists"
            )
    new_volunteer=volunteer.model_dump()
    new_volunteer["email"]=str(volunteer.email)
    new_volunteer["id"]=len(volunteers)+1
    volunteers.append(new_volunteer)

    return{
        "messege":"volunteer registeres successfully",
        "volunteer":new_volunteer
    }

@router.get("/")
def list_volunteers():
    return volunteers