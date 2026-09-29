"""
Comprehensive Test Suite for FitBuddy Platform
Tests schemas, database models, CRUD, AI services, and FastAPI HTTP routes.
Can be executed directly via `python test_fitbuddy.py` or `pytest test_fitbuddy.py`.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure test database is used
os.environ["DATABASE_URL"] = "sqlite:///./test_fitbuddy.db"
os.environ["DEBUG"] = "False"

from app.database import Base, get_db
from app.main import app
from app import crud, schemas, models
from app.services import workout_service, nutrition_service, gemini_service

# Setup test DB
TEST_DB_URL = "sqlite:///./test_fitbuddy.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_1_user_schema_validation():
    """Validates user creation constraints and field boundary checks."""
    print("Testing 1: User schema validation constraints...")
    valid = schemas.UserCreate(
        name="Jordan Lee",
        age=26,
        gender="Non-Binary",
        height=172.0,
        weight=65.0,
        fitness_goal="Strength",
        fitness_level="Beginner",
        workout_intensity="Moderate",
        workout_duration=45,
        available_days=4,
        equipment="Dumbbells",
        preferred_workout_type="Functional Strength",
        dietary_preference="Omnivore",
        limitations="None"
    )
    assert valid.name == "Jordan Lee"
    assert valid.age == 26

    # Invalid age (under 14) should fail validation
    failed = False
    try:
        schemas.UserCreate(
            name="Young",
            age=10,
            gender="Male",
            height=150.0,
            weight=40.0,
            fitness_goal="Fitness",
            fitness_level="Beginner",
            workout_intensity="Low",
            workout_duration=30,
            available_days=3,
            equipment="Bodyweight"
        )
    except Exception:
        failed = True
    assert failed, "Underage user (age 10) was expected to fail validation"
    print("  ✓ User schema validation passed.")


def test_2_database_user_crud():
    """Tests creating, fetching, and updating a user in SQLite."""
    print("Testing 2: Database User CRUD...")
    db = TestingSessionLocal()
    user_in = schemas.UserCreate(
        name="Elena Rostova",
        age=31,
        gender="Female",
        height=168.0,
        weight=61.0,
        fitness_goal="Muscle Building",
        fitness_level="Intermediate",
        workout_intensity="High",
        workout_duration=50,
        available_days=5,
        equipment="Commercial Gym",
        preferred_workout_type="Hypertrophy",
        dietary_preference="Vegetarian",
        limitations="Mild shoulder impingement"
    )
    user = crud.create_user(db, user_in)
    assert user.id is not None
    assert user.name == "Elena Rostova"
    assert user.limitations == "Mild shoulder impingement"

    # Fetch user
    fetched = crud.get_user(db, user.id)
    assert fetched is not None
    assert fetched.fitness_goal == "Muscle Building"
    db.close()
    print("  ✓ Database user CRUD passed.")


def test_3_workout_service_generation():
    """Tests generating a 7-day workout plan and verifying schema integrity."""
    print("Testing 3: Workout Service Generation...")
    db = TestingSessionLocal()
    user = crud.get_latest_user(db)
    assert user is not None

    plan = workout_service.generate_and_save_workout_plan(db, user.id)
    assert plan is not None
    assert plan.version == 1

    parsed = plan.get_parsed_data()
    assert "schedule" in parsed
    assert len(parsed["schedule"]) == 7
    # Day 1 check
    day1 = parsed["schedule"][0]
    assert "day" in day1
    assert "focus" in day1
    assert "exercises" in day1
    assert len(day1["exercises"]) > 0
    assert "warmup" in day1
    assert "cooldown" in day1

    # Check PlanVersion record created
    versions = crud.get_plan_versions(db, plan.id)
    assert len(versions) == 1
    assert versions[0].version == 1
    db.close()
    print("  ✓ Workout Service Generation passed.")


def test_4_feedback_adaptation_loop():
    """Tests submitting feedback and generating a new plan version (V1 -> V2)."""
    print("Testing 4: Feedback Adaptation Loop...")
    db = TestingSessionLocal()
    user = crud.get_latest_user(db)
    plan = crud.get_latest_workout_plan(db, user.id)
    assert plan is not None
    assert plan.version == 1

    feedback_msg = "The workout was too difficult; please lower sets and increase rest time."
    updated_plan = workout_service.adapt_workout_plan_with_feedback(
        db,
        user_id=user.id,
        workout_plan_id=plan.id,
        feedback_text=feedback_msg
    )

    assert updated_plan.version == 2
    # Verify version history has 2 records
    versions = crud.get_plan_versions(db, updated_plan.id)
    assert len(versions) == 2
    # Check feedback record
    feedbacks = crud.get_plan_feedback(db, updated_plan.id)
    assert len(feedbacks) == 1
    assert feedbacks[0].feedback_text == feedback_msg
    db.close()
    print("  ✓ Feedback adaptation (v1 -> v2) passed.")


def test_5_nutrition_service_generation():
    """Tests nutrition, hydration, and sleep protocol generation."""
    print("Testing 5: Nutrition Service Generation...")
    db = TestingSessionLocal()
    user = crud.get_latest_user(db)
    guide = nutrition_service.generate_and_save_nutrition_guide(db, user.id)
    assert guide is not None
    parsed = guide.get_parsed_data()
    assert "macronutrients" in parsed
    assert "hydration_guidelines" in parsed
    assert "sleep_optimization" in parsed
    db.close()
    print("  ✓ Nutrition service generation passed.")


def test_6_fastapi_web_routes():
    """Tests all web HTML endpoints with HTTP status codes."""
    print("Testing 6: Web Routes & Status Codes...")
    # Home Page
    res = client.get("/")
    assert res.status_code == 200
    assert "FitBuddy" in res.text

    # Profile Page
    res = client.get("/profile")
    assert res.status_code == 200
    assert "Fitness Profile" in res.text

    # Submit Profile Form
    res = client.post(
        "/profile",
        data={
            "name": "Tom Brady",
            "age": 45,
            "gender": "Male",
            "height": 193.0,
            "weight": 102.0,
            "fitness_goal": "Endurance",
            "fitness_level": "Advanced",
            "workout_intensity": "High",
            "workout_duration": 60,
            "available_days": 5,
            "equipment": "Full Commercial Gym",
            "preferred_workout_type": "Mobility & Conditioning",
            "dietary_preference": "Omnivore",
            "limitations": "None",
            "generate_now": "true"
        },
        follow_redirects=False
    )
    assert res.status_code == 303
    assert "/workout" in res.headers["location"]

    # Workout Page
    res = client.get("/workout")
    assert res.status_code == 200
    assert "Day" in res.text

    # Nutrition Page
    res = client.get("/nutrition")
    assert res.status_code == 200

    # Feedback Page
    res = client.get("/feedback")
    assert res.status_code == 200

    # History Page
    res = client.get("/history")
    assert res.status_code == 200

    # Admin Dashboard
    res = client.get("/admin")
    assert res.status_code == 200
    assert "Admin Dashboard" in res.text

    # Admin Demo Seeder
    res = client.post("/admin/seed-demo", follow_redirects=False)
    assert res.status_code == 303

    # Health Probe
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("  ✓ Web routes and status codes passed.")


def test_7_rest_api_endpoints():
    """Tests JSON REST API endpoints."""
    print("Testing 7: REST API Endpoints...")
    # Create User via API
    res = client.post("/api/users", json={
        "name": "API Tester",
        "age": 25,
        "gender": "Female",
        "height": 165.0,
        "weight": 58.0,
        "fitness_goal": "General Fitness",
        "fitness_level": "Beginner",
        "workout_intensity": "Low",
        "workout_duration": 30,
        "available_days": 3,
        "equipment": "Bodyweight Only",
        "preferred_workout_type": "Yoga & Bodyweight",
        "dietary_preference": "Vegan",
        "limitations": "None"
    })
    assert res.status_code == 201
    user_id = res.json()["id"]

    # Generate Workout Plan via API
    res = client.post("/api/workouts/generate", json={"user_id": user_id})
    assert res.status_code == 200
    plan_id = res.json()["id"]
    assert res.json()["version"] == 1

    # Submit Feedback via API
    res = client.post("/api/feedback", json={
        "user_id": user_id,
        "workout_plan_id": plan_id,
        "feedback_text": "Need more bodyweight progressions"
    })
    assert res.status_code == 200
    assert res.json()["version"] == 2
    print("  ✓ REST API endpoints passed.")


def main():
    print("=" * 60)
    print("Starting FitBuddy Automated Test Suite...")
    print("=" * 60)
    test_1_user_schema_validation()
    test_2_database_user_crud()
    test_3_workout_service_generation()
    test_4_feedback_adaptation_loop()
    test_5_nutrition_service_generation()
    test_6_fastapi_web_routes()
    test_7_rest_api_endpoints()
    print("=" * 60)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY! (7/7 suites passed)")
    print("=" * 60)


if __name__ == "__main__":
    main()
