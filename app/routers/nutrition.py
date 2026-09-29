import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas, models
from app.services import nutrition_service
from app.routers.users import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Nutrition & Recovery"])
templates = Jinja2Templates(directory="app/templates")


# ==========================================
# Web Page Routes
# ==========================================

@router.get("/nutrition", response_class=HTMLResponse)
async def view_nutrition_page(
    request: Request,
    generate_for: Optional[int] = None,
    success: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Renders the nutrition and recovery assistant page.
    Displays calorie and macro targets, meal timing, hydration targets, and sleep tips.
    """
    current_user_id = generate_for or get_current_user_id(request, db)
    user = crud.get_user(db, current_user_id) if current_user_id else None

    # Handle automatic generation request
    if generate_for and user:
        try:
            nutrition_service.generate_and_save_nutrition_guide(db, user.id)
            return RedirectResponse(
                url="/nutrition?success=Customized+nutrition+and+recovery+strategy+generated!",
                status_code=status.HTTP_303_SEE_OTHER
            )
        except Exception as e:
            logger.error(f"Error auto-generating nutrition: {e}")
            error = f"Error generating nutrition: {str(e)}"

    nutrition_guide = None
    guide_data = None

    if user:
        nutrition_guide = crud.get_latest_nutrition_guide(db, user.id)
        if nutrition_guide:
            guide_data = nutrition_guide.get_parsed_data()

    return templates.TemplateResponse(
        request=request,
        name="nutrition.html",
        context={
            "user": user,
            "nutrition_guide": nutrition_guide,
            "guide_data": guide_data,
            "success": success,
            "error": error,
            "active_tab": "nutrition"
        }
    )


@router.post("/nutrition/generate")
async def handle_generate_nutrition(
    request: Request,
    user_id: int = Form(...),
    plan_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Triggers generation of personalized nutrition and recovery tips."""
    user = crud.get_user(db, user_id)
    if not user:
        return RedirectResponse(
            url="/profile?error=Please+set+up+your+fitness+profile+first",
            status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        nutrition_service.generate_and_save_nutrition_guide(db, user.id, plan_id)
        return RedirectResponse(
            url="/nutrition?success=Nutrition+and+recovery+guidance+generated+successfully!",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as exc:
        logger.error(f"Failed to generate nutrition guidance: {exc}")
        return RedirectResponse(
            url=f"/nutrition?error=Generation+failed:+{str(exc)}",
            status_code=status.HTTP_303_SEE_OTHER
        )


# ==========================================
# REST API Endpoints
# ==========================================

@router.post("/api/nutrition/generate", response_model=schemas.NutritionGuideResponse)
async def api_generate_nutrition(
    req: schemas.WorkoutPlanCreate,
    plan_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """API endpoint to generate nutrition guidance."""
    try:
        guide = nutrition_service.generate_and_save_nutrition_guide(db, req.user_id, plan_id)
        return {
            "id": guide.id,
            "user_id": guide.user_id,
            "plan_id": guide.workout_plan_id,
            "guide_data": guide.get_parsed_data(),
            "created_at": guide.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/nutrition/user/{user_id}", response_model=schemas.NutritionGuideResponse)
async def api_get_user_nutrition(user_id: int, db: Session = Depends(get_db)):
    """API endpoint to retrieve latest nutrition guide for a user."""
    guide = crud.get_latest_nutrition_guide(db, user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="No nutrition guide found for user")
    return {
        "id": guide.id,
        "user_id": guide.user_id,
        "plan_id": guide.workout_plan_id,
        "guide_data": guide.get_parsed_data(),
        "created_at": guide.created_at
    }
