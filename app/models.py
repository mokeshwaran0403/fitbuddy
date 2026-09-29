from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    height = Column(Float, nullable=False)  # in cm
    weight = Column(Float, nullable=False)  # in kg
    fitness_goal = Column(String(100), nullable=False)
    fitness_level = Column(String(50), nullable=False)
    workout_intensity = Column(String(50), nullable=False)
    workout_duration = Column(Integer, nullable=False)  # in minutes
    available_days = Column(Integer, nullable=False)  # days per week (1-7)
    equipment = Column(String(200), nullable=False)
    preferred_workout_type = Column(String(100), nullable=True, default="Mixed")
    dietary_preference = Column(String(100), nullable=False, default="Omnivore")
    limitations = Column(Text, nullable=True, default="None")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workout_plans = relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan", order_by="desc(WorkoutPlan.created_at)")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    nutrition_guides = relationship("NutritionGuide", back_populates="user", cascade="all, delete-orphan", order_by="desc(NutritionGuide.created_at)")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_data = Column(Text, nullable=False)  # JSON-encoded workout plan
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="workout_plans")
    versions = relationship("PlanVersion", back_populates="workout_plan", cascade="all, delete-orphan", order_by="asc(PlanVersion.version)")
    feedbacks = relationship("Feedback", back_populates="workout_plan", cascade="all, delete-orphan")

    def get_parsed_data(self):
        """Safely returns parsed JSON dict of the plan data."""
        try:
            return json.loads(self.plan_data)
        except Exception:
            return {}


class PlanVersion(Base):
    __tablename__ = "plan_versions"

    id = Column(Integer, primary_key=True, index=True)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    plan_data = Column(Text, nullable=False)  # JSON-encoded workout plan
    reason = Column(Text, nullable=True)  # Feedback or modification reason
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    workout_plan = relationship("WorkoutPlan", back_populates="versions")

    def get_parsed_data(self):
        try:
            return json.loads(self.plan_data)
        except Exception:
            return {}


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False)
    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="feedbacks")
    workout_plan = relationship("WorkoutPlan", back_populates="feedbacks")


class NutritionGuide(Base):
    __tablename__ = "nutrition_guides"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True)
    guide_data = Column(Text, nullable=False)  # JSON-encoded nutrition guidance
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="nutrition_guides")

    def get_parsed_data(self):
        try:
            return json.loads(self.guide_data)
        except Exception:
            return {}
