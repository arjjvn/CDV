from datetime import date, time, datetime, timedelta, timezone
from typing import Literal, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from Backend.models import User
from Backend.database_dependency import get_db
from Backend.auth.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()

Role = Literal["admin", "volunteer", "coordinator"]


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["volunteer", "coordinator"] = "volunteer"

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    phone: Optional[str] = None
    district: Optional[str] = None
    place: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None

    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None

    skill1: Optional[str] = None
    skill2: Optional[str] = None
    skill3: Optional[str] = None
    years_experience: Optional[int] = Field(default=None, ge=0, le=100)
    previous_experience: Optional[str] = None

    available_from: Optional[time] = None
    available_to: Optional[time] = None
    languages: Optional[str] = None

    organization: Optional[str] = None
    region: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    role: Optional[Role] = None


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def user_response(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "is_approved": user.is_approved,
        "profile_image": user.profile_image,
    }


@router.post("/register", status_code=201)
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db),
):
    normalized_email = str(user.email).strip().lower()

    existing_user = (
        db.query(User).filter(User.email.ilike(normalized_email)).first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    base_username = (
        f"{user.first_name.strip()}_{user.last_name.strip()}"
    ).lower()

    username = base_username[:50]
    counter = 1

    while db.query(User).filter(User.username == username).first():
        suffix = str(counter)
        username = f"{base_username[:50 - len(suffix)]}{suffix}"
        counter += 1

    data = user.model_dump(exclude={"email", "password", "role"})

    new_user = User(
        username=username,
        email=normalized_email,
        hashed_password=hash_password(user.password),
        role=user.role,
        is_approved=(user.role == "volunteer"),
        **data,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="A user with these details already exists."
        )

    message = (
        "Registration successful. You can now log in."
        if new_user.role == "volunteer"
        else "Registration received. Await administrator approval."
    )

    return {
        "message": message,
        "user": user_response(new_user),
    }


@router.post("/login")
def login_user(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = str(credentials.email).strip().lower()

    user = db.query(User).filter(User.email.ilike(normalized_email)).first()

    if user is None or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if credentials.role and user.role != credentials.role:
        raise HTTPException(
            status_code=403,
            detail="Selected role does not match this account.",
        )

    # Volunteers can log in without admin approval.
    # Coordinators and admins require approval.
    if user.role in ("coordinator", "admin") and not user.is_approved:
        raise HTTPException(
            status_code=403,
            detail="Account not approved. Please contact an administrator.",
        )

    access_token = create_access_token(user)

    # The dashboard routes authenticate using this cookie.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set True when deployed with HTTPS.
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_response(user),
    }


@router.get("/logout")
@router.post("/logout")
def logout_user(response: Response):
    res = RedirectResponse(url="/pages/login.html", status_code=303)
    res.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax",
    )
    return res


@router.get("/me")
def get_my_profile(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload["sub"])

    except (
        jwt.PyJWTError,
        ValueError,
        TypeError,
        KeyError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User profile not found.",
        )

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "phone": user.phone,
        "district": user.district,
        "place": user.place,
        "address": user.address,
        "pincode": user.pincode,
        "date_of_birth": user.date_of_birth,
        "gender": user.gender,
        "blood_group": user.blood_group,
        "skill1": user.skill1,
        "skill2": user.skill2,
        "skill3": user.skill3,
        "years_experience": user.years_experience,
        "previous_experience": user.previous_experience,
        "available_from": (
            user.available_from.strftime("%H:%M") if user.available_from else None
        ),
        "available_to": (
            user.available_to.strftime("%H:%M") if user.available_to else None
        ),
        "languages": user.languages,
        "organization": user.organization,
        "region": user.region,
        "is_approved": user.is_approved,
        "profile_image": user.profile_image,
    }
