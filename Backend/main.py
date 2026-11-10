from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from Backend.auth import routes as auth_routes
from Backend.auth import protected
from Backend.database import create_tables
from Backend import models
from Backend.routers import chatbot
from Backend.routers import dashboards
from Backend.routers import health
from Backend.routers import emergency

app = FastAPI(
    title="Community Disaster Volunteer Hub (CDVH)",
    description="API for AI-assisted disaster volunteer matching, deep learning triage, and coordination.",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
PAGES_DIR = FRONTEND_DIR / "pages"


@app.on_event("startup")
def startup():
    create_tables()


# ----------------------------------------------------------------------
# ROOT & TEMPLATE PAGE REDIRECTS (PREVENT RAW STATIC JINJA ACCESS)
# ----------------------------------------------------------------------

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/pages/volunteer-dashboard.html")
def redirect_volunteer_page():
    return RedirectResponse(url="/volunteers/dashboard", status_code=303)


@app.get("/pages/coordinator-dashboard.html")
def redirect_coordinator_page():
    return RedirectResponse(url="/coordinator/dashboard", status_code=303)


@app.get("/pages/admin-dashboard.html")
def redirect_admin_page():
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/pages/profile.html")
def redirect_profile_page():
    return RedirectResponse(url="/profile", status_code=303)


# ----------------------------------------------------------------------
# STATIC FILE MOUNTS
# ----------------------------------------------------------------------

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")


# ----------------------------------------------------------------------
# ROUTER INCLUSIONS
# ----------------------------------------------------------------------

app.include_router(health.router)
app.include_router(emergency.router)
app.include_router(auth_routes.router)
app.include_router(protected.router)
app.include_router(chatbot.router)
app.include_router(dashboards.router)
