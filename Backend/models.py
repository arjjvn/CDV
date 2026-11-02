from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    Boolean,
    Date,
    Time,
    Text,
    DateTime,
    Float,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from Backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(String(50), nullable=False, default="volunteer")
    is_approved = Column(Boolean, default=False)
    profile_image = Column(String(255), nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    skills = Column(JSON, nullable=False)
    location = Column(String(100), nullable=False)


class Disaster(Base):
    __tablename__ = "disasters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    disaster_type = Column(String(100), nullable=False)  # Flood, Landslide, Fire, Cyclone, etc.
    description = Column(Text, nullable=True)
    district = Column(String(100), nullable=True)
    place = Column(String(100), nullable=True)
    severity = Column(String(50), default="Medium")  # Low, Medium, High, Urgent
    status = Column(String(50), default="Active")     # Active, Monitoring, Resolved
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    tasks = relationship("Task", back_populates="disaster", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(150), nullable=True)
    urgency = Column(String(50), default="Active")  # Urgent, Active, Pending, Resolved
    status = Column(String(50), default="active")    # active, resolved, pending
    required_volunteer_count = Column(Integer, default=1)
    skills_required = Column(String(255), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    disaster = relationship("Disaster", back_populates="tasks")
    assignments = relationship("Assignment", back_populates="task", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    volunteer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    match_score = Column(Float, nullable=True)
    status = Column(String(50), default="assigned")  # assigned, in_progress, completed
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    task = relationship("Task", back_populates="assignments")
    volunteer = relationship("User", foreign_keys=[volunteer_user_id])
    assigner = relationship("User", foreign_keys=[assigned_by])
