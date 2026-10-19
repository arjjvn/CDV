from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI
from Backend.routers import health,volunteers
from Backend.auth import routes as auth_routes
from Backend.auth import protected
from Backend.routers import chatbot

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
PAGES_DIR = FRONTEND_DIR / "pages"

app=FastAPI(
    title="Community Disaster Volunteer Hub",
    description="API for disaster volunteer coordination",
    version="1.0.0"
)
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")

app.include_router(health.router)
app.include_router(volunteers.router)
app.include_router(auth_routes.router)
app.include_router(protected.router)
app.include_router(chatbot.router)