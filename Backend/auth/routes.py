import os
from datetime import datetime,timedelta,timezone
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter,HTTPException
from pwdlib import PasswordHash
from pydantic import BaseModel,EmailStr,Field

router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hash = PasswordHash.recommended()

load_dotenv()
SECRET_KEY=os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing. Set it in your .env file!!")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

#Temp storage, acc disappear when the server restart 
users=[]

class UserRegister(BaseModel):
    username: str=Field(min_length=3,max_length=50)
    email: EmailStr
    password: str=Field(min_length=8,max_length=128)

@router.post("/register",status_code=201)
def register_user(user:UserRegister):
    for existing_user in users:
        if (
            existing_user["email"].lower()==str(user.email).lower()
        ):
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists!"
            )
    new_user={
        "id":len(users)+1,
        "username":user.username,
        "email":str(user.email),
        "hashed_password": hash_password(user.password)
        
    }
    users.append(new_user)

    return{
        "message":"User registered successfully",
        "user":{
            "id":new_user["id"],
            "username":new_user["username"],
            "email":new_user["email"]
        }
    }
def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

class UserLogin(BaseModel):
    email:EmailStr
    password:str=Field(min_length=1,max_length=128)

@router.post("/login")
def login_user(credentials:UserLogin):
    user=next(
        (
            item for item in users
            if item["email"].lower()==str(credentials.email).lower()
        ),
        None
    )
    if user is None or not verify_password(
        credentials.password,
        user["hashed_password"]
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
            "sub":str(user["id"]),
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
