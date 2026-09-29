import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app import crud, models
from app.services import gemini_service
from app.schemas import WorkoutPlanData

logger = logging.getLogger(__name__)


def generate_and_save_workout_plan(db: Session, user_id: int) -> models.WorkoutPlan:
    """
    Generates an AI workout plan for a given user, validates the schema,
    and stores it in the database.
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
        "workout_duration": user.workout_duration,
        "available_days": user.available_days,
        "equipment": user.equipment,
        "preferred_workout_type": user.preferred_workout_type,
        "dietary_preference": user.dietary_preference,
        "limitations": user.limitations,
    }

    # Generate plan from AI service
    raw_plan_dict = gemini_service.generate_workout_plan(user_dict)

    # Validate with Pydantic model
    try:
        validated_plan = WorkoutPlanData(**raw_plan_dict)
        plan_dict = validated_plan.model_dump()
    except Exception as e:
        logger.warning(f"Workout plan validation warning: {e}. Saving sanitized dictionary.")
        plan_dict = raw_plan_dict

    # Store in database
    workout_plan = crud.create_workout_plan(db, user_id=user.id, plan_dict=plan_dict)
    return workout_plan


def adapt_workout_plan_with_feedback(
    db: Session,
    user_id: int,
    workout_plan_id: int,
    feedback_text: str
) -> models.WorkoutPlan:
    """
    Records user feedback, asks Gemini to adapt the workout plan,
    validates the new plan, and archives it as a new plan version.
    """
    workout_plan = crud.get_workout_plan(db, workout_plan_id)
    if not workout_plan:
        raise ValueError(f"Workout plan {workout_plan_id} not found.")

    user = crud.get_user(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found.")

    # 1. Save user feedback
    crud.create_feedback(
        db,
        user_id=user.id,
        workout_plan_id=workout_plan.id,
        feedback_text=feedback_text
    )

    user_dict = {
        "fitness_goal": user.fitness_goal,
        "fitness_level": user.fitness_level,
        "limitations": user.limitations,
        "equipment": user.equipment,
    }

    current_data = workout_plan.get_parsed_data()

    # 2. Call AI service to adapt
    adapted_raw = gemini_service.update_workout_plan(current_data, feedback_text, user_dict)

    # 3. Validate
    try:
        validated = WorkoutPlanData(**adapted_raw)
        adapted_dict = validated.model_dump()
    except Exception as e:
        logger.warning(f"Adapted plan validation warning: {e}")
        adapted_dict = adapted_raw

    # 4. Save new version
    updated_plan = crud.update_workout_plan_version(
        db,
        workout_plan_id=workout_plan.id,
        new_plan_dict=adapted_dict,
        reason=f"User feedback: {feedback_text.strip()[:100]}"
    )

    return updated_plan
