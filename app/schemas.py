from datetime import datetime
from typing import List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==========================================
# User Schemas
# ==========================================

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    age: int = Field(..., ge=14, le=100, description="Age must be between 14 and 100")
    gender: str = Field(..., min_length=1, max_length=50, description="Gender identity")
    height: float = Field(..., gt=50.0, lt=260.0, description="Height in centimeters (50 - 260 cm)")
    weight: float = Field(..., gt=25.0, lt=350.0, description="Weight in kilograms (25 - 350 kg)")
    fitness_goal: str = Field(..., min_length=2, max_length=100, description="Primary fitness goal")
    fitness_level: str = Field(..., min_length=2, max_length=50, description="Beginner, Intermediate, or Advanced")
    workout_intensity: str = Field(..., min_length=2, max_length=50, description="Low, Moderate, or High")
    workout_duration: int = Field(..., ge=15, le=180, description="Workout duration in minutes (15 - 180 mins)")
    available_days: int = Field(..., ge=1, le=7, description="Available days per week (1 - 7 days)")
    equipment: str = Field(..., min_length=2, max_length=200, description="Available equipment or Bodyweight")
    preferred_workout_type: Optional[str] = Field("Mixed", max_length=100, description="Preferred workout style (e.g. HIIT, Strength, Yoga, Cardio)")
    dietary_preference: str = Field("Omnivore", min_length=2, max_length=100, description="Dietary style (e.g. Vegan, Vegetarian, Keto, Omnivore)")
    limitations: Optional[str] = Field("None", max_length=500, description="Injuries or physical limitations")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or blank")
        return v

    @field_validator("limitations", mode="before")
    @classmethod
    def sanitize_limitations(cls, v: Optional[str]) -> str:
        if not v or not str(v).strip():
            return "None"
        return str(v).strip()


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=14, le=100)
    gender: Optional[str] = None
    height: Optional[float] = Field(None, gt=50.0, lt=260.0)
    weight: Optional[float] = Field(None, gt=25.0, lt=350.0)
    fitness_goal: Optional[str] = None
    fitness_level: Optional[str] = None
    workout_intensity: Optional[str] = None
    workout_duration: Optional[int] = Field(None, ge=15, le=180)
    available_days: Optional[int] = Field(None, ge=1, le=7)
    equipment: Optional[str] = None
    preferred_workout_type: Optional[str] = None
    dietary_preference: Optional[str] = None
    limitations: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Workout Plan Structured Schemas
# ==========================================

class ExerciseItem(BaseModel):
    name: str = Field(..., description="Exercise name")
    sets: Union[int, str] = Field(..., description="Number of sets (e.g. 3 or '3-4')")
    repetitions: Union[int, str] = Field(..., description="Target repetitions or duration (e.g. 10 or '8-12' or '30 sec')")
    rest_seconds: Union[int, str] = Field(60, description="Rest period in seconds")
    notes: Optional[str] = Field(None, description="Form tips or exercise alternatives")


class DayPlan(BaseModel):
    day: str = Field(..., description="E.g. Day 1, Monday")
    focus: str = Field(..., description="Target muscle group or workout focus (e.g. Upper Body, Active Recovery)")
    warmup: Union[List[str], str] = Field(..., description="Warm-up routine 5-10 mins")
    exercises: List[ExerciseItem] = Field(default_factory=list, description="List of exercises for this day")
    cooldown: Union[List[str], str] = Field(..., description="Cool-down routine 5 mins")
    recovery: str = Field(..., description="Recovery recommendations for the day")


class WorkoutPlanData(BaseModel):
    program_title: str = Field("FitBuddy 7-Day Personalized Plan", description="Name of the program")
    overview: str = Field(..., description="Summary of the weekly program tailored to user")
    target_goal: str = Field(..., description="User's targeted fitness goal")
    schedule: List[DayPlan] = Field(..., description="7-day schedule")
    safety_notes: List[str] = Field(default_factory=list, description="Safety considerations tailored to limitations")
    disclaimer: str = Field(
        "Disclaimer: FitBuddy provides automated fitness guidance for educational purposes only. It is not medical advice. Consult a qualified physician before starting any new exercise routine.",
        description="Health and safety disclaimer"
    )


class WorkoutPlanCreate(BaseModel):
    user_id: int


class WorkoutPlanResponse(BaseModel):
    id: int
    user_id: int
    version: int
    plan_data: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Feedback & Plan Version Schemas
# ==========================================

class FeedbackCreate(BaseModel):
    user_id: int
    workout_plan_id: int
    feedback_text: str = Field(..., min_length=3, max_length=1000, description="User's workout experience and feedback")

    @field_validator("feedback_text")
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Feedback cannot be blank")
        return v


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    workout_plan_id: int
    feedback_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanVersionResponse(BaseModel):
    id: int
    workout_plan_id: int
    version: int
    plan_data: Dict[str, Any]
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Nutrition & Recovery Schemas
# ==========================================

class MacroSplit(BaseModel):
    protein: str = Field(..., description="Recommended protein intake in grams or %")
    carbohydrates: str = Field(..., description="Recommended carbohydrate intake")
    fats: str = Field(..., description="Recommended healthy fats intake")


class NutritionGuideData(BaseModel):
    summary: str = Field(..., description="Nutritional strategy aligned with user's goal")
    daily_calories_estimate: str = Field(..., description="Estimated caloric baseline or range")
    macronutrients: MacroSplit = Field(..., description="Target macro breakdown")
    meal_timing: List[str] = Field(default_factory=list, description="Pre/post workout nutrition and timing")
    recommended_foods: List[str] = Field(default_factory=list, description="Goal-friendly food suggestions")
    foods_to_moderate: List[str] = Field(default_factory=list, description="Foods to minimize or moderate")
    hydration_guidelines: str = Field(..., description="Daily water intake targets and electrolyte guidance")
    recovery_protocol: List[str] = Field(default_factory=list, description="Active recovery, stretching, mobility tips")
    sleep_optimization: List[str] = Field(default_factory=list, description="Sleep duration, sleep hygiene, and circadian habits")
    disclaimer: str = Field(
        "Disclaimer: FitBuddy nutrition guidance provides general wellness concepts. It is not a medical dietary prescription. Consult a registered dietitian or physician for specific medical nutrition therapy.",
        description="Nutrition disclaimer"
    )


class NutritionGuideResponse(BaseModel):
    id: int
    user_id: int
    plan_id: Optional[int]
    guide_data: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
