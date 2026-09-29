from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas, models

router = APIRouter(tags=["Users"])
templates = Jinja2Templates(directory="app/templates")


def get_current_user_id(request: Request, db: Session) -> Optional[int]:
    """Helper to detect active user ID from query param, cookie, or fallback to latest user."""
    # 1. Query parameter
    user_id_param = request.query_params.get("user_id")
    if user_id_param and user_id_param.isdigit():
        return int(user_id_param)

    # 2. Cookie
    cookie_id = request.cookies.get("fitbuddy_user_id")
    if cookie_id and cookie_id.isdigit():
        return int(cookie_id)

    # 3. Fallback to latest registered user
    latest_user = crud.get_latest_user(db)
    return latest_user.id if latest_user else None


# ==========================================
# Web Page Routes
# ==========================================

@router.get("/profile", response_class=HTMLResponse)
async def view_profile_page(request: Request, db: Session = Depends(get_db)):
    """Renders user profile creation or edit page."""
    current_id = get_current_user_id(request, db)
    user = crud.get_user(db, current_id) if current_id else None

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "active_tab": "profile"
        }
    )


@router.post("/profile")
async def handle_profile_form(
    request: Request,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Form(None),
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    fitness_goal: str = Form(...),
    fitness_level: str = Form(...),
    workout_intensity: str = Form(...),
    workout_duration: int = Form(...),
    available_days: int = Form(...),
    equipment: str = Form(...),
    preferred_workout_type: Optional[str] = Form("Mixed"),
    dietary_preference: str = Form("Omnivore"),
    limitations: Optional[str] = Form("None"),
    generate_now: Optional[str] = Form(None)
):
    """Handles HTML form submission for user registration or profile update."""
    try:
        user_create = schemas.UserCreate(
            name=name,
            age=age,
            gender=gender,
            height=height,
            weight=weight,
            fitness_goal=fitness_goal,
            fitness_level=fitness_level,
            workout_intensity=workout_intensity,
            workout_duration=workout_duration,
            available_days=available_days,
            equipment=equipment,
            preferred_workout_type=preferred_workout_type or "Mixed",
            dietary_preference=dietary_preference,
            limitations=limitations or "None"
        )
    except Exception as validation_err:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "error": str(validation_err),
                "active_tab": "profile"
            },
            status_code=400
        )

    if user_id:
        # Update existing user
        user = crud.update_user(db, user_id, schemas.UserUpdate(**user_create.model_dump()))
        if not user:
            user = crud.create_user(db, user_create)
    else:
        user = crud.create_user(db, user_create)

    # Determine redirect destination
    if generate_now == "true":
        redirect_url = f"/workout?generate_for={user.id}"
    else:
        redirect_url = f"/workout?user_id={user.id}&success=Profile+saved+successfully"

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("fitbuddy_user_id", str(user.id), max_age=86400 * 30)
    return response


# ==========================================
# REST API Endpoints
# ==========================================

@router.post("/api/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def api_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """API endpoint to create a new user profile with validation."""
    return crud.create_user(db, user)


@router.get("/api/users/{user_id}", response_model=schemas.UserResponse)
async def api_get_user(user_id: int, db: Session = Depends(get_db)):
    """API endpoint to retrieve user profile by ID."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/api/users/{user_id}", response_model=schemas.UserResponse)
async def api_update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """API endpoint to update user profile."""
    updated = crud.update_user(db, user_id, user_update)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.get("/api/users", response_model=List[schemas.UserResponse])
async def api_list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """API endpoint to list users."""
    return crud.get_all_users(db, skip=skip, limit=limit)
