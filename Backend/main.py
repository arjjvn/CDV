from fastapi import FastAPI
from Backend.routers import health,volunteers
from Backend.auth import routes as auth_routes
from Backend.auth import protected
from Backend.database import create_tables
from Backend import models

app=FastAPI(
    title="Community Disaster Volunteer Hub",
    description="API for disaster volunteer coordination",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    create_tables()

@app.get("/")
def home():
    return{
        "message": "Welcome to Disaster Volunteer Hub!",
        "status": "running"
    }

app.include_router(health.router)
app.include_router(volunteers.router)
app.include_router(auth_routes.router)
app.include_router(protected.router)