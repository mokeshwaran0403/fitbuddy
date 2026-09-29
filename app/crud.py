import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import User, WorkoutPlan, PlanVersion, Feedback, NutritionGuide
from app.schemas import UserCreate, UserUpdate


# ==========================================
# User CRUD
# ==========================================

def create_user(db: Session, user_data: UserCreate) -> User:
    """Creates a new user record."""
    db_user = User(
        name=user_data.name.strip(),
        age=user_data.age,
        gender=user_data.gender,
        height=user_data.height,
        weight=user_data.weight,
        fitness_goal=user_data.fitness_goal,
        fitness_level=user_data.fitness_level,
        workout_intensity=user_data.workout_intensity,
        workout_duration=user_data.workout_duration,
        available_days=user_data.available_days,
        equipment=user_data.equipment,
        preferred_workout_type=user_data.preferred_workout_type or "Mixed",
        dietary_preference=user_data.dietary_preference,
        limitations=user_data.limitations or "None"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Retrieves a single user by primary key ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_latest_user(db: Session) -> Optional[User]:
    """Retrieves the most recently created or active user."""
    return db.query(User).order_by(desc(User.id)).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Retrieves a paginated list of all users."""
    return db.query(User).order_by(desc(User.created_at)).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Updates an existing user profile."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_dict = user_update.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(db_user, field, value)

    db_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Deletes a user and cascades related records."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


# ==========================================
# Workout Plan CRUD
# ==========================================

def create_workout_plan(db: Session, user_id: int, plan_dict: dict, version: int = 1) -> WorkoutPlan:
    """Creates a new workout plan and automatically archives Version 1 into plan_versions."""
    plan_json = json.dumps(plan_dict)
    workout_plan = WorkoutPlan(
        user_id=user_id,
        plan_data=plan_json,
        version=version,
        created_at=datetime.now(timezone.utc)
    )
    db.add(workout_plan)
    db.commit()
    db.refresh(workout_plan)

    # Archive initial version
    initial_version = PlanVersion(
        workout_plan_id=workout_plan.id,
        version=version,
        plan_data=plan_json,
        reason="Initial AI generation based on user fitness profile",
        created_at=workout_plan.created_at
    )
    db.add(initial_version)
    db.commit()

    return workout_plan


def get_workout_plan(db: Session, plan_id: int) -> Optional[WorkoutPlan]:
    """Retrieves a workout plan by its ID."""
    return db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()


def get_latest_workout_plan(db: Session, user_id: int) -> Optional[WorkoutPlan]:
    """Retrieves the newest workout plan for a specific user."""
    return db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).order_by(desc(WorkoutPlan.created_at)).first()


def get_user_workout_plans(db: Session, user_id: int) -> List[WorkoutPlan]:
    """Retrieves all workout plans for a user."""
    return db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).order_by(desc(WorkoutPlan.created_at)).all()


def get_all_workout_plans(db: Session, skip: int = 0, limit: int = 100) -> List[WorkoutPlan]:
    """Retrieves all workout plans across users for admin or metrics."""
    return db.query(WorkoutPlan).order_by(desc(WorkoutPlan.created_at)).offset(skip).limit(limit).all()


def update_workout_plan_version(
    db: Session,
    workout_plan_id: int,
    new_plan_dict: dict,
    reason: str
) -> Optional[WorkoutPlan]:
    """
    Updates a workout plan with an adapted AI plan based on user feedback.
    Increments the version number and records a historical entry in plan_versions.
    """
    plan = get_workout_plan(db, workout_plan_id)
    if not plan:
        return None

    new_version_num = plan.version + 1
    new_plan_json = json.dumps(new_plan_dict)

    # Update active plan
    plan.plan_data = new_plan_json
    plan.version = new_version_num

    # Add historical version
    version_entry = PlanVersion(
        workout_plan_id=plan.id,
        version=new_version_num,
        plan_data=new_plan_json,
        reason=reason,
        created_at=datetime.now(timezone.utc)
    )
    db.add(version_entry)
    db.commit()
    db.refresh(plan)
    return plan


# ==========================================
# Feedback CRUD
# ==========================================

def create_feedback(db: Session, user_id: int, workout_plan_id: int, feedback_text: str) -> Feedback:
    """Stores user feedback for a specific workout plan."""
    feedback = Feedback(
        user_id=user_id,
        workout_plan_id=workout_plan_id,
        feedback_text=feedback_text.strip(),
        created_at=datetime.now(timezone.utc)
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_plan_feedback(db: Session, workout_plan_id: int) -> List[Feedback]:
    """Retrieves all feedback entries for a workout plan."""
    return db.query(Feedback).filter(Feedback.workout_plan_id == workout_plan_id).order_by(desc(Feedback.created_at)).all()


def get_all_feedback(db: Session, limit: int = 100) -> List[Feedback]:
    """Retrieves all feedback entries across the system."""
    return db.query(Feedback).order_by(desc(Feedback.created_at)).limit(limit).all()


# ==========================================
# Plan Version CRUD
# ==========================================

def get_plan_versions(db: Session, workout_plan_id: int) -> List[PlanVersion]:
    """Retrieves version history for a given workout plan in ascending version order."""
    return db.query(PlanVersion).filter(PlanVersion.workout_plan_id == workout_plan_id).order_by(desc(PlanVersion.version)).all()


def get_plan_version_by_id(db: Session, version_id: int) -> Optional[PlanVersion]:
    """Retrieves a specific plan version by ID."""
    return db.query(PlanVersion).filter(PlanVersion.id == version_id).first()


# ==========================================
# Nutrition Guide CRUD
# ==========================================

def create_nutrition_guide(db: Session, user_id: int, guide_dict: dict, plan_id: Optional[int] = None) -> NutritionGuide:
    """Saves generated nutrition and recovery guidance for a user."""
    guide = NutritionGuide(
        user_id=user_id,
        workout_plan_id=plan_id,
        guide_data=json.dumps(guide_dict),
        created_at=datetime.now(timezone.utc)
    )
    db.add(guide)
    db.commit()
    db.refresh(guide)
    return guide


def get_latest_nutrition_guide(db: Session, user_id: int) -> Optional[NutritionGuide]:
    """Retrieves the most recent nutrition guide for a user."""
    return db.query(NutritionGuide).filter(NutritionGuide.user_id == user_id).order_by(desc(NutritionGuide.created_at)).first()


def get_all_nutrition_guides(db: Session, limit: int = 100) -> List[NutritionGuide]:
    """Retrieves recent nutrition guides."""
    return db.query(NutritionGuide).order_by(desc(NutritionGuide.created_at)).limit(limit).all()
