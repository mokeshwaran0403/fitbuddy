import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app import crud, models
from app.services import gemini_service
from app.schemas import NutritionGuideData

logger = logging.getLogger(__name__)


def generate_and_save_nutrition_guide(
    db: Session,
    user_id: int,
    workout_plan_id: Optional[int] = None
) -> models.NutritionGuide:
    """
    Generates tailored nutrition, hydration, and sleep recovery tips for a user,
    validates the output, and persists it in SQLite.
    """
    user = crud.get_user(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found.")

    user_dict = {
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "height": user.height,
        "weight": user.weight,
        "fitness_goal": user.fitness_goal,
        "fitness_level": user.fitness_level,
        "workout_intensity": user.workout_intensity,
        "dietary_preference": user.dietary_preference,
        "limitations": user.limitations
    }

    raw_guide = gemini_service.generate_nutrition_tips(user_dict)

    try:
        validated = NutritionGuideData(**raw_guide)
        guide_dict = validated.model_dump()
    except Exception as e:
        logger.warning(f"Nutrition guide validation warning: {e}. Saving sanitized data.")
        guide_dict = raw_guide

    guide = crud.create_nutrition_guide(
        db,
        user_id=user.id,
        guide_dict=guide_dict,
        plan_id=workout_plan_id
    )

    return guide
