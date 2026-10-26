from sqlalchemy import Column, Integer, String, JSON, Boolean, Date, Time, Text, DateTime, ForeignKey, func
from Backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(String(50), nullable=False, default="volunteer")
    is_approved = Column(Boolean, default=False)

    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    district = Column(String(100), nullable=True)
    place = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    pincode = Column(String(20), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    blood_group = Column(String(5), nullable=True)

    skill1 = Column(String(50), nullable=True)
    skill2 = Column(String(50), nullable=True)
    skill3 = Column(String(50), nullable=True)
    years_experience = Column(Integer, nullable=True)
    previous_experience = Column(Text, nullable=True)
    available_from = Column(Time, nullable=True)
    available_to = Column(Time, nullable=True)
    languages = Column(String(100), nullable=True)

    organization = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)

    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 
class Volunteer(Base):
    __tablename__ = "volunteers"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    email=Column(String(255),unique=True,index=True,nullable=False)
    skills=Column(JSON,nullable=False)
    location=Column(String(100),nullable=False)