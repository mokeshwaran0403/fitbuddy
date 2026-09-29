import os
import json
import re
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configurable environment variables for models
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_WORKOUT_MODEL = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-1.5-pro").strip()
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-1.5-flash").strip()

# Try loading the modern google.genai SDK, or legacy google.generativeai
HAVE_GOOGLE_GENAI = False
HAVE_LEGACY_GENAI = False

try:
    from google import genai
    from google.genai import types
    HAVE_GOOGLE_GENAI = True
except ImportError:
    try:
        import google.generativeai as legacy_genai
        HAVE_LEGACY_GENAI = True
    except ImportError:
        pass


def is_api_key_configured() -> bool:
    """Returns True if a non-placeholder Gemini API key is configured."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(key and key != "your_gemini_api_key_here" and key != "your_api_key_here")


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Strips markdown code blocks, extracts JSON object, and parses safely.
    """
    if not raw_text:
        raise ValueError("Empty response received from AI model")

    cleaned = raw_text.strip()

    # Remove markdown code fences if present: ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Find the outermost JSON block if there's conversational prefix/suffix
    start_bracket = cleaned.find("{")
    end_bracket = cleaned.rfind("}")

    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        cleaned = cleaned[start_bracket : end_bracket + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as err:
        logger.error(f"JSON decode error: {err}. Raw text: {raw_text[:300]}")
        raise ValueError(f"Failed to parse structured JSON from AI output: {err}")


def call_gemini_api(prompt: str, model_name: str, system_instruction: Optional[str] = None) -> str:
    """
    Executes Gemini API call using either modern google.genai or fallback legacy SDK.
    Enforces JSON response mode where possible.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_"):
        raise ValueError("GEMINI_API_KEY is not configured in .env file.")

    # 1. Attempt using modern google-genai SDK
    if HAVE_GOOGLE_GENAI:
        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            if response and response.text:
                return response.text
        except Exception as e:
            logger.warning(f"google.genai SDK call failed ({e}), attempting fallback...")

    # 2. Attempt using legacy google.generativeai SDK
    if HAVE_LEGACY_GENAI:
        try:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction if system_instruction else None
            )
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.4}
            )
            if response and response.text:
                return response.text
        except Exception as e:
            logger.error(f"google.generativeai SDK call failed: {e}")
            raise e

    raise RuntimeError("No working Gemini SDK or API key found to complete the request.")


# ==========================================
# Rule-Based / Intelligent Offline Fallback
# ==========================================

def get_intelligent_fallback_workout(user: dict) -> dict:
    """
    Constructs a medically-conservative, structured 7-day fitness routine
    when Gemini API key is missing or offline.
    """
    goal = user.get("fitness_goal", "General Fitness")
    level = user.get("fitness_level", "Beginner")
    duration = user.get("workout_duration", 45)
    equipment = user.get("equipment", "Bodyweight")
    limitations = user.get("limitations", "None")
    days_per_week = min(max(int(user.get("available_days", 4)), 1), 7)

    # Tailored exercise selection
    has_dumbbells = "dumbbell" in equipment.lower() or "weights" in equipment.lower() or "gym" in equipment.lower()
    has_knee_issues = "knee" in limitations.lower()
    has_back_issues = "back" in limitations.lower()

    # Define conservative warm-ups
    general_warmup = [
        "Arm circles & torso twists (2 mins)",
        "Cat-Cow and Bird-Dog mobility (3 mins)",
        "Light marching or jumping jacks (2 mins)" if not has_knee_issues else "Seated or low-impact leg raises (2 mins)"
    ]

    general_cooldown = [
        "Hamstring and quad gentle static stretches (2 mins)",
        "Chest opener & doorway shoulder stretch (2 mins)",
        "Deep diaphragmatic breathing (2 mins)"
    ]

    # Pre-crafted daily templates
    schedule = []
    daily_templates = [
        {
            "day": "Day 1",
            "focus": "Upper Body & Posture",
            "exercises": [
                {"name": "Dumbbell Floor Press" if has_dumbbells else "Incline Wall/Knee Push-ups", "sets": 3, "repetitions": 10, "rest_seconds": 60, "notes": "Keep core tight, elbows at 45 degrees"},
                {"name": "Dumbbell Bent-Over Row" if has_dumbbells else "Prone Cobra / Towel Rows", "sets": 3, "repetitions": 12, "rest_seconds": 60, "notes": "Squeeze shoulder blades together gently"},
                {"name": "Dumbbell Overhead Press" if has_dumbbells else "Pike Push-up or Hand Release Press", "sets": 3, "repetitions": 8, "rest_seconds": 60, "notes": "Maintain neutral spine"},
                {"name": "Forearm Plank (or Kneeling Plank)", "sets": 3, "repetitions": "30 sec", "rest_seconds": 45, "notes": "Do not let lower back sag"}
            ],
            "recovery": "Hydrate well and stretch upper back and chest before bed."
        },
        {
            "day": "Day 2",
            "focus": "Lower Body & Core Mobility",
            "exercises": [
                {"name": "Goblet Squat (Box Squat)" if not has_knee_issues else "Glute Bridges (Joint-Friendly)", "sets": 3, "repetitions": 10, "rest_seconds": 60, "notes": "Drive through heels"},
                {"name": "Romanian Deadlift" if not has_back_issues else "Hip Thrusts from floor", "sets": 3, "repetitions": 10, "rest_seconds": 60, "notes": "Hinge hips backward with soft knees"},
                {"name": "Reverse Lunges (or Step-ups)", "sets": 3, "repetitions": "8 each leg", "rest_seconds": 60, "notes": "Avoid slamming knees on floor"},
                {"name": "Dead Bug Core Holds", "sets": 3, "repetitions": "10 each side", "rest_seconds": 45, "notes": "Keep lower back flush with floor"}
            ],
            "recovery": "Light 15-minute walk to promote circulation and reduce leg stiffness."
        },
        {
            "day": "Day 3",
            "focus": "Active Recovery & Mobility Flow",
            "exercises": [
                {"name": "World's Greatest Stretch", "sets": 2, "repetitions": "5 each side", "rest_seconds": 45, "notes": "Move fluidly and breathe deeply"},
                {"name": "Thoracic Spine Foam Rolling or Foam Rotations", "sets": 2, "repetitions": 10, "rest_seconds": 45, "notes": "Relieve mid-back tension"},
                {"name": "Calf & Ankle Mobility Drills", "sets": 2, "repetitions": 12, "rest_seconds": 30, "notes": "Enhances lower body stability"}
            ],
            "recovery": "Focus on high-quality sleep, gentle hydration, and 8 hours of rest."
        },
        {
            "day": "Day 4",
            "focus": "Cardio-Conditioning & Full Body Tone",
            "exercises": [
                {"name": "Brisk Incline Walking or Low-Impact Intervals", "sets": 4, "repetitions": "3 mins active / 1 min easy", "rest_seconds": 60, "notes": "Maintain conversational breathing pace"},
                {"name": "Dumbbell Farmers Walk" if has_dumbbells else "Bodyweight Bear Crawl Holds", "sets": 3, "repetitions": "30 sec", "rest_seconds": 60, "notes": "Keep shoulders back and core engaged"},
                {"name": "Bodyweight Good Mornings", "sets": 3, "repetitions": 12, "rest_seconds": 45, "notes": "Warm the posterior chain"}
            ],
            "recovery": "Refuel with lean protein and colorful vegetables."
        },
        {
            "day": "Day 5",
            "focus": "Pull & Posterior Chain Strength",
            "exercises": [
                {"name": "Single-Arm Dumbbell Row" if has_dumbbells else "Doorframe Inverted Rows", "sets": 3, "repetitions": 10, "rest_seconds": 60, "notes": "Controlled tempo"},
                {"name": "Glute Bridges with 2-sec Pause", "sets": 3, "repetitions": 12, "rest_seconds": 45, "notes": "Squeeze glutes at peak"},
                {"name": "Side Planks", "sets": 3, "repetitions": "20 sec each", "rest_seconds": 45, "notes": "Strengthen obliques and spinal stabilizers"}
            ],
            "recovery": "Epsom salt warm bath or gentle stretching session."
        },
        {
            "day": "Day 6",
            "focus": "Functional Fitness & Core",
            "exercises": [
                {"name": "Step-Downs or Box Step-Ups", "sets": 3, "repetitions": 10, "rest_seconds": 60, "notes": "Focus on balance and knee alignment"},
                {"name": "Push-up Variations (Elevated or Regular)", "sets": 3, "repetitions": 8, "rest_seconds": 60, "notes": "Stop 2 reps short of total failure"},
                {"name": "Bird-Dog Extensions", "sets": 3, "repetitions": "10 each", "rest_seconds": 45, "notes": "Reach hand and opposite foot straight"}
            ],
            "recovery": "Hydrate with electrolyte balance and take an easy stroll."
        },
        {
            "day": "Day 7",
            "focus": "Full Rest & Regeneration",
            "exercises": [
                {"name": "Gentle Leisure Walk", "sets": 1, "repetitions": "20-30 mins", "rest_seconds": 0, "notes": "Enjoy fresh air and natural sunlight"},
                {"name": "Full Body Static Stretching", "sets": 1, "repetitions": "10 mins", "rest_seconds": 0, "notes": "Hold each stretch comfortably without pain"}
            ],
            "recovery": "Meal prep for the upcoming week and ensure restorative 8-hour sleep."
        }
    ]

    # Adjust active vs rest days based on available_days
    for i, day_tmpl in enumerate(daily_templates):
        day_num = i + 1
        day_copy = dict(day_tmpl)
        if day_num > days_per_week:
            day_copy["focus"] = "Rest & Active Recovery"
            day_copy["exercises"] = [
                {"name": "Gentle Mobility & Stretching", "sets": 1, "repetitions": "15 mins", "rest_seconds": 0, "notes": "Gentle range of motion"},
                {"name": "Mindful Walking or Meditation", "sets": 1, "repetitions": "20 mins", "rest_seconds": 0, "notes": "Promotes mental and physical recovery"}
            ]
            day_copy["recovery"] = "Complete physical rest. Focus on nutritious hydration and restful sleep."
        day_copy["warmup"] = general_warmup
        day_copy["cooldown"] = general_cooldown
        schedule.append(day_copy)

    safety = [
        f"Customized for {level} fitness level with conservative progression.",
        f"Session lengths target {duration} minutes inclusive of warm-up and cool-down.",
        f"Consideration of noted limitations: '{limitations}'. Exercises maintain joint safety and avoid strain."
    ]

    return {
        "program_title": f"FitBuddy 7-Day {goal} Protocol",
        "overview": f"A scientifically balanced 7-day fitness regimen customized for {user.get('name', 'User')}, targeting {goal} at a {level} level across {days_per_week} active days per week with {equipment}.",
        "target_goal": goal,
        "schedule": schedule,
        "safety_notes": safety,
        "disclaimer": "Disclaimer: FitBuddy provides automated fitness guidance for educational and wellness purposes only. It is not medical advice. Consult a physician before beginning any physical exercise."
    }


def get_intelligent_fallback_nutrition(user: dict) -> dict:
    """
    Constructs high-quality general wellness nutrition and recovery guidance
    based on the user's metrics and dietary preferences.
    """
    weight = float(user.get("weight", 70))
    height = float(user.get("height", 175))
    age = int(user.get("age", 28))
    gender = user.get("gender", "Other").lower()
    goal = user.get("fitness_goal", "General Fitness")
    diet = user.get("dietary_preference", "Omnivore")

    # Basal Metabolic Rate (Mifflin-St Jeor formula)
    if "female" in gender:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    # Activity multiplier estimate (1.4 - 1.6)
    tdee = int(bmr * 1.45)

    if "muscle" in goal.lower() or "strength" in goal.lower():
        target_calories = f"{tdee + 250} - {tdee + 450} kcal (Modest surplus for lean gains)"
        protein_g = f"{int(weight * 1.8)} - {int(weight * 2.2)} g"
        carbs = "40-45% of total intake"
        fats = "25-30% of healthy dietary fats"
    elif "weight" in goal.lower() or "loss" in goal.lower() or "fat" in goal.lower():
        target_calories = f"{max(tdee - 400, 1300)} - {tdee - 200} kcal (Sustainable conservative deficit)"
        protein_g = f"{int(weight * 1.6)} - {int(weight * 2.0)} g (Satiety & lean tissue preservation)"
        carbs = "30-35% complex whole carbohydrates"
        fats = "25-30% essential healthy fats"
    else:
        target_calories = f"{tdee - 100} - {tdee + 100} kcal (Energy balance & maintenance)"
        protein_g = f"{int(weight * 1.4)} - {int(weight * 1.8)} g"
        carbs = "40-50% complex carbohydrates"
        fats = "25-30% balanced healthy fats"

    water_target = round(weight * 0.035, 1)

    diet_foods = {
        "Vegan": ["Tofu, tempeh, edamame, lentils", "Quinoa, brown rice, rolled oats", "Chia seeds, walnuts, avocado", "Spinach, kale, bell peppers"],
        "Vegetarian": ["Greek yogurt, cottage cheese, eggs", "Lentils, chickpeas, tempeh", "Nuts, seeds, extra virgin olive oil", "Diverse seasonal vegetables"],
        "Keto": ["Wild salmon, chicken thighs, grass-fed beef", "Avocados, macadamia nuts, olive oil", "Broccoli, cauliflower, asparagus, zucchini"],
        "Omnivore": ["Lean poultry, eggs, wild salmon, Greek yogurt", "Oats, sweet potatoes, brown rice", "Avocado, almonds, olive oil", "Cruciferous greens and berries"]
    }
    recommended = diet_foods.get(diet, diet_foods["Omnivore"])

    return {
        "summary": f"Targeted nutritional strategy supporting '{goal}' under a {diet} lifestyle, prioritizing sustained cellular energy, muscle recovery, and metabolic balance.",
        "daily_calories_estimate": target_calories,
        "macronutrients": {
            "protein": f"{protein_g} daily",
            "carbohydrates": carbs,
            "fats": fats
        },
        "meal_timing": [
            "Pre-Workout (60-90 mins prior): Light meal with easily digestible carbohydrates and moderate protein.",
            "Post-Workout (within 2 hours): Balanced meal containing 20-35g protein to kickstart muscle protein synthesis.",
            "Even Distribution: Spread protein across 3-4 meals to optimize absorption."
        ],
        "recommended_foods": recommended,
        "foods_to_moderate": [
            "Ultra-processed convenience foods with high saturated oils",
            "Sugar-sweetened beverages and concentrated fruit juices",
            "Excessive alcohol consumption which impairs protein synthesis and deep REM sleep",
            "Heavy, high-fat fried meals immediately preceding training sessions"
        ],
        "hydration_guidelines": f"Consume approximately {water_target} to {round(water_target + 0.8, 1)} Liters of water daily. Increase by 500ml on intense training days with an electrolyte pinch during high perspiration.",
        "recovery_protocol": [
            "10-15 minute post-session cool down and gentle dynamic mobility.",
            "Contrast showers or warm magnesium salt baths for muscular relaxation.",
            "Gentle active recovery walks (20 mins) on non-lifting days.",
            "Consistent daily stretching focusing on hip flexors, hamstrings, and thoracic spine."
        ],
        "sleep_optimization": [
            "Target 7.5 to 9 hours of uninterrupted sleep per night for optimal hormonal recovery.",
            "Maintain a dark, cool bedroom environment (approx. 18-20°C / 65-68°F).",
            "Discontinue blue-light emitting screens 45 minutes before sleep.",
            "Establish consistent sleep and wake times even on weekends."
        ],
        "disclaimer": "Disclaimer: FitBuddy nutrition guidance provides general educational wellness recommendations. It is not medical nutrition therapy or disease treatment. Consult a licensed physician or registered dietitian before making drastic nutritional adjustments."
    }


# ==========================================
# Core AI Services
# ==========================================

def generate_workout_plan(user_data: dict) -> dict:
    """
    Generates a personalized 7-day workout plan using Gemini 1.5 Pro / configured model.
    Falls back gracefully if API key is not configured or network fails.
    """
    if not is_api_key_configured():
        logger.info("Gemini API key not configured. Using intelligent rule-based generator.")
        return get_intelligent_fallback_workout(user_data)

    system_instruction = (
        "You are FitBuddy, an elite, certified master fitness coach and exercise physiologist. "
        "Your duty is to generate safe, effective, personalized, science-backed 7-day fitness plans. "
        "SAFETY MANDATE: Strictly avoid dangerous movements. If the user mentions any injury or limitation, "
        "treat it conservatively: provide joint-friendly alternatives and never prescribe exercises that strain the injured area. "
        "Never make medical diagnosis. Always output strict, valid JSON conforming to the requested schema."
    )

    prompt = f"""
Create a comprehensive 7-day personalized workout plan for the following user:
- Name: {user_data.get('name', 'Fitness Enthusiast')}
- Age: {user_data.get('age')} years old
- Gender: {user_data.get('gender')}
- Height: {user_data.get('height')} cm
- Weight: {user_data.get('weight')} kg
- Fitness Goal: {user_data.get('fitness_goal')}
- Fitness Level: {user_data.get('fitness_level')}
- Workout Intensity: {user_data.get('workout_intensity')}
- Available Workout Days: {user_data.get('available_days')} days per week
- Target Workout Duration: {user_data.get('workout_duration')} minutes per session
- Available Equipment: {user_data.get('equipment')}
- Preferred Workout Type: {user_data.get('preferred_workout_type', 'Mixed')}
- Dietary Style: {user_data.get('dietary_preference', 'Omnivore')}
- Physical Limitations / Injuries: {user_data.get('limitations', 'None')}

Output MUST be a single valid JSON object with EXACTLY this structure:
{{
  "program_title": "string",
  "overview": "string",
  "target_goal": "{user_data.get('fitness_goal')}",
  "schedule": [
    {{
      "day": "Day 1",
      "focus": "Muscle group or theme (e.g. Upper Body Strength or Rest & Mobility)",
      "warmup": ["Warm-up drill 1", "Warm-up drill 2"],
      "exercises": [
        {{
          "name": "Exercise Name",
          "sets": 3,
          "repetitions": "10-12",
          "rest_seconds": 60,
          "notes": "Coaching cues, tempo, or conservative modification"
        }}
      ],
      "cooldown": ["Cool-down stretch 1", "Cool-down stretch 2"],
      "recovery": "Daily recovery guidance and hydration tip"
    }}
    // Repeat for all 7 days (Day 1 through Day 7)
  ],
  "safety_notes": ["Safety guideline tailored to user and their limitations"],
  "disclaimer": "Disclaimer: FitBuddy provides automated fitness guidance for educational purposes only. It is not medical advice. Consult a qualified physician before starting any new exercise routine."
}}
Ensure the plan accurately reflects {user_data.get('available_days')} training days and designates the remaining days as Rest / Active Recovery.
"""

    try:
        model_name = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-1.5-pro").strip()
        raw_output = call_gemini_api(prompt, model_name=model_name, system_instruction=system_instruction)
        parsed = clean_json_response(raw_output)

        # Validate minimum expected structure
        if "schedule" not in parsed or not isinstance(parsed["schedule"], list):
            raise ValueError("AI response missed the 'schedule' list")

        return parsed
    except Exception as exc:
        logger.error(f"Error calling Gemini workout generation ({exc}). Falling back to internal engine.")
        fallback = get_intelligent_fallback_workout(user_data)
        fallback["safety_notes"].append(f"Note: Generated via built-in intelligent planner (Gemini notice: {str(exc)[:120]})")
        return fallback


def generate_nutrition_tips(user_data: dict) -> dict:
    """
    Generates personalized nutrition, hydration, and sleep guidance using Gemini Fast model.
    """
    if not is_api_key_configured():
        logger.info("Gemini API key not configured. Using intelligent rule-based nutrition generator.")
        return get_intelligent_fallback_nutrition(user_data)

    system_instruction = (
        "You are FitBuddy's sports nutrition and recovery advisor. "
        "Provide scientific, balanced, general wellness nutrition guidance. "
        "Strictly avoid medical prescriptions, extreme starvation diets, or dangerous supplements. "
        "Always output strict valid JSON."
    )

    prompt = f"""
Generate comprehensive nutrition, hydration, and sleep recovery guidance for this user:
- Goal: {user_data.get('fitness_goal')}
- Age: {user_data.get('age')}
- Gender: {user_data.get('gender')}
- Height: {user_data.get('height')} cm
- Weight: {user_data.get('weight')} kg
- Dietary Preference: {user_data.get('dietary_preference')}
- Fitness Level: {user_data.get('fitness_level')}
- Workout Intensity: {user_data.get('workout_intensity')}

Return a single valid JSON object formatted exactly as:
{{
  "summary": "Overview of nutritional strategy",
  "daily_calories_estimate": "Estimated calories with explanation",
  "macronutrients": {{
    "protein": "Grams or % breakdown",
    "carbohydrates": "Grams or % breakdown",
    "fats": "Grams or % breakdown"
  }},
  "meal_timing": ["Guideline on pre-workout", "Guideline on post-workout"],
  "recommended_foods": ["Food 1", "Food 2", "Food 3", "Food 4"],
  "foods_to_moderate": ["Food to limit 1", "Food to limit 2"],
  "hydration_guidelines": "Water and electrolyte recommendations",
  "recovery_protocol": ["Active recovery tip 1", "Active recovery tip 2"],
  "sleep_optimization": ["Sleep habit 1", "Sleep habit 2"],
  "disclaimer": "Disclaimer: FitBuddy nutrition guidance provides general wellness concepts. It is not a medical dietary prescription. Consult a registered dietitian or physician for specific medical nutrition therapy."
}}
"""

    try:
        model_name = os.getenv("GEMINI_FAST_MODEL", "gemini-1.5-flash").strip()
        raw_output = call_gemini_api(prompt, model_name=model_name, system_instruction=system_instruction)
        parsed = clean_json_response(raw_output)
        if "macronutrients" not in parsed:
            raise ValueError("Parsed JSON missing 'macronutrients'")
        return parsed
    except Exception as exc:
        logger.error(f"Error calling Gemini nutrition generation ({exc}). Falling back to internal engine.")
        return get_intelligent_fallback_nutrition(user_data)


def update_workout_plan(current_plan: dict, feedback_text: str, user_data: dict) -> dict:
    """
    Updates an existing workout plan based on user feedback (e.g. 'Day 3 too hard', 'less time', 'knee pain').
    Gemini modifies the exercises, volume, or rest times while retaining progression.
    """
    if not is_api_key_configured():
        logger.info("Using intelligent rule-based plan adaptation.")
        # Modify the existing plan based on feedback keywords
        updated = dict(current_plan)
        lower_fb = feedback_text.lower()
        days = updated.get("schedule", [])

        for day in days:
            for ex in day.get("exercises", []):
                if "too hard" in lower_fb or "difficult" in lower_fb or "easier" in lower_fb:
                    if isinstance(ex.get("sets"), int) and ex["sets"] > 2:
                        ex["sets"] = ex["sets"] - 1
                    ex["rest_seconds"] = int(ex.get("rest_seconds", 60)) + 30
                    ex["notes"] = (ex.get("notes") or "") + " [Adapted: Reduced volume per feedback]"
                elif "too easy" in lower_fb or "harder" in lower_fb or "more intense" in lower_fb:
                    if isinstance(ex.get("sets"), int):
                        ex["sets"] = ex["sets"] + 1
                    ex["notes"] = (ex.get("notes") or "") + " [Adapted: Intensified per feedback]"
                elif "knee" in lower_fb:
                    if "squat" in ex.get("name", "").lower() or "lunge" in ex.get("name", "").lower():
                        ex["name"] = "Glute Bridge / Box Step (Knee Friendly)"
                        ex["notes"] = "Modified to protect knees per user feedback"
                elif "time" in lower_fb or "shorter" in lower_fb:
                    ex["rest_seconds"] = 45
                    ex["notes"] = (ex.get("notes") or "") + " [Adapted: Time-efficient superset]"

        updated["overview"] = updated.get("overview", "") + f" (Updated in Version response to feedback: '{feedback_text[:60]}...')"
        return updated

    system_instruction = (
        "You are FitBuddy, updating an existing 7-day workout plan based on specific user feedback. "
        "Modify the workout volume, exercise selections, or rest periods to directly address their feedback. "
        "Strictly adhere to safety and conservative injury management. Output valid JSON in the exact same schema."
    )

    prompt = f"""
Here is the user's current 7-day workout plan:
{json.dumps(current_plan, indent=2)}

User Fitness Profile:
- Goal: {user_data.get('fitness_goal')}
- Fitness Level: {user_data.get('fitness_level')}
- Limitations: {user_data.get('limitations')}
- Equipment: {user_data.get('equipment')}

The user has submitted this direct feedback on their current plan:
"{feedback_text}"

TASK:
Analyze the feedback carefully and regenerate an adapted 7-day plan that:
1. Directly addresses their feedback (e.g., if too difficult, reduce sets/reps or extend rest; if injury noted, replace offending exercise; if less time, condense exercises).
2. Preserves the overall weekly structure and target goal.
3. Keeps the exact same JSON schema as the original plan (program_title, overview, target_goal, schedule with day, focus, warmup, exercises, cooldown, recovery, safety_notes, disclaimer).

Return ONLY the updated valid JSON object.
"""

    try:
        model_name = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-1.5-pro").strip()
        raw_output = call_gemini_api(prompt, model_name=model_name, system_instruction=system_instruction)
        parsed = clean_json_response(raw_output)
        if "schedule" not in parsed:
            raise ValueError("Parsed JSON missing 'schedule'")
        return parsed
    except Exception as exc:
        logger.error(f"Error adapting workout plan with Gemini ({exc}). Using internal rule adaptation.")
        return update_workout_plan(current_plan, feedback_text, user_data)
