from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI
from Backend.routers import health,volunteers
from Backend.auth import routes as auth_routes
from Backend.auth import protected
from Backend.database import create_tables
from Backend import models
from Backend.routers import chatbot
from Backend.routers import dashboards

app=FastAPI(
    title="Community Disaster Volunteer Hub",
    description="API for disaster volunteer coordination",
    version="1.0.0"
)
BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
PAGES_DIR = FRONTEND_DIR / "pages"

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")

@app.on_event("startup")
def startup():
    create_tables()

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")

app.include_router(health.router)
app.include_router(volunteers.router)
app.include_router(auth_routes.router)
app.include_router(protected.router)
app.include_router(chatbot.router)
app.include_router(dashboards.router)