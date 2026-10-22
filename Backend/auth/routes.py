from datetime import datetime,timedelta,timezone
import jwt
from fastapi import APIRouter,HTTPException,Depends
from pwdlib import PasswordHash
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy.orm import Session
from Backend.auth.models import User
from Backend.database_dependency import get_db
from Backend.auth.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hash = PasswordHash.recommended()



class UserRegister(BaseModel):
    username: str=Field(min_length=3,max_length=50)
    email: EmailStr
    password: str=Field(min_length=8,max_length=128)

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

@router.post("/register",status_code=201)
def register_user(
    user:UserRegister,
    db:Session=Depends(get_db)
):
    normalized_email=str(user.email).lower()
    existing_user=(
        db.query(User).filter(User.email.ilike(normalized_email)).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists!"
        )
  
    new_user=User(
        username=user.username,
        email=normalized_email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise
    return{
        "message":"User registered successfully",
        "user":{
            "id":new_user.id,
            "username":new_user.username,
            "email":new_user.email,
        },
    }


class UserLogin(BaseModel):
    email:EmailStr
    password:str=Field(min_length=1,max_length=128)

@router.post("/login")
def login_user(
    credentials:UserLogin,
    db: Session=Depends(get_db),
):
    normalized_email=str(credentials.email).lower()
    user=(db.query(User).filter(User.email.ilike(normalized_email)).first())
  
    if user is None or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    expires_at=datetime.now(timezone.utc)+timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token=jwt.encode(
        {
            "sub":str(user.id),
            "exp":expires_at
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return{
        "access_token":access_token,
        "token_type":"bearer",
        "expires_in":ACCESS_TOKEN_EXPIRE_MINUTES*60
    }
