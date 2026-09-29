import os
import logging
from typing import Optional
from collections import Counter
from fastapi import APIRouter, Depends, Request, Form, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, models, schemas
from app.services import workout_service, nutrition_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")

ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "fitbuddy-admin-secret-2025")


@router.get("/admin", response_class=HTMLResponse)
async def view_admin_dashboard(
    request: Request,
    key: Optional[str] = None,
    inspect_plan_id: Optional[int] = None,
    success: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Renders the FitBuddy Admin Dashboard.
    Shows metrics, users, workout plans, plan versions, and feedback.
    """
    users = crud.get_all_users(db, limit=100)
    workout_plans = crud.get_all_workout_plans(db, limit=100)
    feedbacks = crud.get_all_feedback(db, limit=50)
    nutrition_guides = crud.get_all_nutrition_guides(db, limit=50)

    # Goal distribution
    goals_counter = Counter([u.fitness_goal for u in users])
    goals_data = dict(goals_counter)

    # Inspect specific plan if requested
    inspected_plan = None
    inspected_plan_data = None
    if inspect_plan_id:
        inspected_plan = crud.get_workout_plan(db, inspect_plan_id)
        if inspected_plan:
            inspected_plan_data = inspected_plan.get_parsed_data()

    # Collect total versions count
    all_versions_count = sum(len(p.versions) for p in workout_plans)

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "users": users,
            "workout_plans": workout_plans,
            "feedbacks": feedbacks,
            "nutrition_guides": nutrition_guides,
            "goals_data": goals_data,
            "total_users": len(users),
            "total_plans": len(workout_plans),
            "total_versions": all_versions_count,
            "total_feedback": len(feedbacks),
            "inspected_plan": inspected_plan,
            "inspected_plan_data": inspected_plan_data,
            "success": success,
            "error": error,
            "active_tab": "admin"
        }
    )


@router.post("/admin/seed-demo")
async def seed_demo_data(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Convenient button on Admin Dashboard to create sample demo profiles
    representing realistic fitness scenarios (beginner fat loss, strength, bodyweight).
    """
    try:
        sample_users = [
            {
                "name": "Sarah Miller",
                "age": 29,
                "gender": "Female",
                "height": 165.0,
                "weight": 68.0,
                "fitness_goal": "Weight Management",
                "fitness_level": "Beginner",
                "workout_intensity": "Low",
                "workout_duration": 35,
                "available_days": 4,
                "equipment": "Dumbbells & Resistance Bands",
                "preferred_workout_type": "Circuit & Low-Impact Cardio",
                "dietary_preference": "Vegetarian",
                "limitations": "Mild lower back tightness after sitting"
            },
            {
                "name": "Marcus Vance",
                "age": 34,
                "gender": "Male",
                "height": 182.0,
                "weight": 86.0,
                "fitness_goal": "Muscle Building",
                "fitness_level": "Intermediate",
                "workout_intensity": "High",
                "workout_duration": 60,
                "available_days": 5,
                "equipment": "Full Commercial Gym (Barbells, Dumbbells, Cables)",
                "preferred_workout_type": "Hypertrophy Push-Pull-Legs",
                "dietary_preference": "Omnivore",
                "limitations": "None"
            },
            {
                "name": "David Chen",
                "age": 42,
                "gender": "Male",
                "height": 174.0,
                "weight": 79.0,
                "fitness_goal": "General Fitness",
                "fitness_level": "Beginner",
                "workout_intensity": "Moderate",
                "workout_duration": 40,
                "available_days": 3,
                "equipment": "Bodyweight Only (At Home)",
                "preferred_workout_type": "Functional Bodyweight & Mobility",
                "dietary_preference": "Omnivore",
                "limitations": "Right knee discomfort during deep knee flexion"
            }
        ]

        created_user = None
        for u in sample_users:
            # Check if user already exists
            existing = db.query(models.User).filter(models.User.name == u["name"]).first()
            if not existing:
                created_user = crud.create_user(db, schemas.UserCreate(**u))
                # Generate a workout plan and nutrition guide for the first demo user
                plan = workout_service.generate_and_save_workout_plan(db, created_user.id)
                nutrition_service.generate_and_save_nutrition_guide(db, created_user.id, plan.id)
            else:
                created_user = existing

        # Set active cookie to the first demo user
        response = RedirectResponse(
            url="/admin?success=Demo+fitness+profiles+and+AI+plans+created+successfully!",
            status_code=status.HTTP_303_SEE_OTHER
        )
        if created_user:
            response.set_cookie("fitbuddy_user_id", str(created_user.id), max_age=86400 * 30)
        return response
    except Exception as exc:
        logger.error(f"Error seeding demo data: {exc}")
        return RedirectResponse(
            url=f"/admin?error=Failed+to+seed+data:+{str(exc)}",
            status_code=status.HTTP_303_SEE_OTHER
        )
