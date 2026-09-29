import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas, models
from app.services import workout_service
from app.routers.users import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workouts"])
templates = Jinja2Templates(directory="app/templates")


# ==========================================
# Web Page Routes
# ==========================================

@router.get("/workout", response_class=HTMLResponse)
async def view_workout_page(
    request: Request,
    plan_id: Optional[int] = None,
    version_id: Optional[int] = None,
    generate_for: Optional[int] = None,
    success: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Renders the workout plan page.
    Displays 7-day interactive day-by-day workout cards, warm-up, cool-down, and recovery.
    """
    current_user_id = generate_for or get_current_user_id(request, db)
    user = crud.get_user(db, current_user_id) if current_user_id else None

    # Handle automatic generation request if triggered from profile page
    if generate_for and user:
        try:
            new_plan = workout_service.generate_and_save_workout_plan(db, user.id)
            return RedirectResponse(
                url=f"/workout?plan_id={new_plan.id}&success=7-Day+personalized+plan+generated+successfully!",
                status_code=status.HTTP_303_SEE_OTHER
            )
        except Exception as e:
            logger.error(f"Error auto-generating plan: {e}")
            error = f"Error generating plan: {str(e)}"

    workout_plan = None
    versions = []
    feedbacks = []
    parsed_plan = None
    selected_version_num = None

    if user:
        if plan_id:
            workout_plan = crud.get_workout_plan(db, plan_id)
        else:
            workout_plan = crud.get_latest_workout_plan(db, user.id)

        if workout_plan:
            versions = crud.get_plan_versions(db, workout_plan.id)
            feedbacks = crud.get_plan_feedback(db, workout_plan.id)

            if version_id:
                # User specifically requested an older archived version
                version_record = crud.get_plan_version_by_id(db, version_id)
                if version_record:
                    parsed_plan = version_record.get_parsed_data()
                    selected_version_num = version_record.version
            if not parsed_plan:
                parsed_plan = workout_plan.get_parsed_data()
                selected_version_num = workout_plan.version

    return templates.TemplateResponse(
        request=request,
        name="workout.html",
        context={
            "user": user,
            "workout_plan": workout_plan,
            "plan_data": parsed_plan,
            "versions": versions,
            "feedbacks": feedbacks,
            "selected_version": selected_version_num,
            "success": success,
            "error": error,
            "active_tab": "workout"
        }
    )


@router.post("/workout/generate")
async def handle_generate_workout(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Triggers generation of a brand new 7-day workout plan."""
    user = crud.get_user(db, user_id)
    if not user:
        return RedirectResponse(
            url="/profile?error=Please+create+or+select+a+profile+first",
            status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        new_plan = workout_service.generate_and_save_workout_plan(db, user.id)
        return RedirectResponse(
            url=f"/workout?plan_id={new_plan.id}&success=Your+personalized+7-Day+plan+is+ready!",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as exc:
        logger.error(f"Failed to generate workout plan: {exc}")
        return RedirectResponse(
            url=f"/workout?error=Generation+failed:+{str(exc)}",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.get("/feedback", response_class=HTMLResponse)
async def view_feedback_page(
    request: Request,
    plan_id: Optional[int] = None,
    success: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Renders the AI plan improvement / feedback page."""
    current_user_id = get_current_user_id(request, db)
    user = crud.get_user(db, current_user_id) if current_user_id else None

    workout_plan = None
    if user:
        if plan_id:
            workout_plan = crud.get_workout_plan(db, plan_id)
        else:
            workout_plan = crud.get_latest_workout_plan(db, user.id)

    feedbacks = crud.get_plan_feedback(db, workout_plan.id) if workout_plan else []

    return templates.TemplateResponse(
        request=request,
        name="feedback.html",
        context={
            "user": user,
            "workout_plan": workout_plan,
            "feedbacks": feedbacks,
            "success": success,
            "error": error,
            "active_tab": "feedback"
        }
    )


@router.post("/feedback")
async def handle_submit_feedback(
    request: Request,
    user_id: int = Form(...),
    workout_plan_id: int = Form(...),
    feedback_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Submits user feedback, triggers Gemini to adapt the workout plan,
    creates a new plan version, and redirects back to view the updated plan.
    """
    if not feedback_text or not feedback_text.strip():
        return RedirectResponse(
            url=f"/feedback?plan_id={workout_plan_id}&error=Please+provide+valid+feedback+text",
            status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        updated_plan = workout_service.adapt_workout_plan_with_feedback(
            db,
            user_id=user_id,
            workout_plan_id=workout_plan_id,
            feedback_text=feedback_text.strip()
        )
        msg = f"Plan+adapted+successfully!+Now+viewing+Version+{updated_plan.version}"
        return RedirectResponse(
            url=f"/workout?plan_id={updated_plan.id}&success={msg}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as exc:
        logger.error(f"Failed to adapt workout plan: {exc}")
        return RedirectResponse(
            url=f"/feedback?plan_id={workout_plan_id}&error=Failed+to+update+plan:+{str(exc)}",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.get("/history", response_class=HTMLResponse)
async def view_history_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Renders the workout plan history and version timeline."""
    current_user_id = get_current_user_id(request, db)
    user = crud.get_user(db, current_user_id) if current_user_id else None

    plans = []
    if user:
        plans = crud.get_user_workout_plans(db, user.id)

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "user": user,
            "plans": plans,
            "active_tab": "history"
        }
    )


# ==========================================
# REST API Endpoints
# ==========================================

@router.post("/api/workouts/generate", response_model=schemas.WorkoutPlanResponse)
async def api_generate_workout(req: schemas.WorkoutPlanCreate, db: Session = Depends(get_db)):
    """API endpoint to generate and return a workout plan."""
    try:
        plan = workout_service.generate_and_save_workout_plan(db, req.user_id)
        return {
            "id": plan.id,
            "user_id": plan.user_id,
            "version": plan.version,
            "plan_data": plan.get_parsed_data(),
            "created_at": plan.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/workouts/{plan_id}", response_model=schemas.WorkoutPlanResponse)
async def api_get_workout(plan_id: int, db: Session = Depends(get_db)):
    """API endpoint to get a workout plan by ID."""
    plan = crud.get_workout_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "version": plan.version,
        "plan_data": plan.get_parsed_data(),
        "created_at": plan.created_at
    }


@router.post("/api/feedback", response_model=schemas.WorkoutPlanResponse)
async def api_submit_feedback(req: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    """API endpoint to submit feedback and get the updated plan version."""
    try:
        updated = workout_service.adapt_workout_plan_with_feedback(
            db,
            user_id=req.user_id,
            workout_plan_id=req.workout_plan_id,
            feedback_text=req.feedback_text
        )
        return {
            "id": updated.id,
            "user_id": updated.user_id,
            "version": updated.version,
            "plan_data": updated.get_parsed_data(),
            "created_at": updated.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
