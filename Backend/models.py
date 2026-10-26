from sqlalchemy import Column, Integer, String, JSON
from Backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
class Volunteer(Base):
    __tablename__ = "volunteers"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    email=Column(String(255),unique=True,index=True,nullable=False)
    skills=Column(JSON,nullable=False)
    location=Column(String(100),nullable=False)