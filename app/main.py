import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# Load environment
load_dotenv()

from app.database import init_db, get_db
from app import crud, models
from app.routers import users, workouts, nutrition, admin
from app.routers.users import get_current_user_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fitbuddy")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables on startup
    logger.info("Initializing FitBuddy Database tables...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down FitBuddy application.")


app = FastAPI(
    title="FitBuddy - Generative AI Fitness Planning Assistant",
    description="A modern, production-ready AI-powered fitness, workout, nutrition, and recovery platform driven by Google Gemini.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Mount static files
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Register routers
app.include_router(users.router)
app.include_router(workouts.router)
app.include_router(nutrition.router)
app.include_router(admin.router)


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    """
    Renders the FitBuddy Landing / Home Page.
    Introduces the AI platform, provides immediate CTAs, displays safety disclaimer,
    and shows active user status if available.
    """
    current_user_id = get_current_user_id(request, db)
    user = crud.get_user(db, current_user_id) if current_user_id else None
    latest_plan = crud.get_latest_workout_plan(db, user.id) if user else None

    # Global stats for landing page social proof
    total_users_count = len(crud.get_all_users(db, limit=500))
    total_plans_count = len(crud.get_all_workout_plans(db, limit=500))

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "latest_plan": latest_plan,
            "total_users": total_users_count,
            "total_plans": total_plans_count,
            "active_tab": "home"
        }
    )


@app.get("/health")
async def health_check():
    """Application health probe."""
    return {"status": "ok", "app": "FitBuddy AI Platform"}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "error_title": "404 - Page Not Found",
            "error_message": "The requested fitness resource could not be found.",
            "active_tab": ""
        },
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "error_title": "Application Notice",
            "error_message": "An unexpected error occurred while processing your fitness data. Please try again or check logs.",
            "active_tab": ""
        },
        status_code=500
    )
