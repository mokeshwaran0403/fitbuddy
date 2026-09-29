# ⚡ FitBuddy — Generative AI Fitness Planning Platform

FitBuddy is a modern, responsive, production-ready Generative AI-powered fitness and nutrition assistant built with **FastAPI**, **Google Gemini AI**, **SQLite**, **SQLAlchemy**, and **Jinja2**.

FitBuddy generates tailored 7-day workout plans, calculates goal-specific nutrition and recovery protocols, and utilizes a generative AI feedback loop to continuously improve and adapt your routines over time.

---

## 🌟 Key Features

1. **Precision 7-Day Workout Generation**:
   - Biomechanically sound routines periodized over 7 days.
   - Dynamic warm-up drills, exact sets, rep schemes, rest countdown periods, and mobility cool-downs.
   - Rest & active recovery day protocols.
2. **Injury-Aware & Medically Conservative Architecture**:
   - Explicit safety filtering for physical limitations (knee, back, shoulder, etc.).
   - Eliminates dangerous axial loading or contraindicated movements.
   - Clear fitness and health disclaimers across all views.
3. **Continuous AI Plan Adaptation Loop**:
   - Users provide natural language feedback (e.g. *"Day 3 was too difficult"*, *"Knee feels sensitive"*, *"Only 30 minutes available"*).
   - Gemini adapts the workout volume, rest times, and exercises.
   - Stores complete plan version history (`v1 → v2 → v3`) without overwriting previous versions.
4. **Goal-Specific Nutrition & Recovery Assistant**:
   - Estimated daily caloric baseline & Mifflin-St Jeor metabolic alignment.
   - Target macronutrient splits (protein, carbohydrates, healthy fats).
   - Pre- and post-workout nutrient timing windows.
   - Goal-aligned food recommendations & foods to moderate.
   - Personalized hydration targets (Liters/day + electrolyte guidance).
   - Muscular recovery & circadian sleep optimization.
5. **Interactive Gym-Ready Web Interface**:
   - Sleek athletic dark mode with glassmorphic cards and electric accents.
   - Interactive exercise checklist with daily progress tracking.
   - In-app interactive rest timer countdown modal with audible completion alert.
   - One-click copy routine to clipboard & print-ready layout.
6. **Telemetry & Admin Dashboard**:
   - Metrics overview: Total Users, Active Plans, Archived Versions, Feedback logs.
   - Goal distribution analytics.
   - Plan Inspector to review user schedules.
   - One-click realistic demo profile seeder for instant demonstration.
7. **Production-Grade Resilience**:
   - Seamless dual-SDK support (`google-genai` and `google-generativeai`).
   - Strict Pydantic v2 data validation schemas.
   - Built-in intelligent offline planner fallback when testing without an API key or during network downtime.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) |
| **Artificial Intelligence** | [Google Gemini API](https://aistudio.google.com/) (`gemini-1.5-pro` & `gemini-1.5-flash`) |
| **Database & ORM** | SQLite 3 + [SQLAlchemy 2.0](https://www.sqlalchemy.org/) |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| **Templating** | [Jinja2](https://jinja.palletsprojects.com/) |
| **Frontend Styling** | Vanilla CSS (Custom Design System, Glassmorphism, Responsive) |
| **Frontend Scripting** | Vanilla JavaScript (ES6+, AudioContext, Local DOM timers) |
| **Configuration** | `python-dotenv` |

---

## 📁 Project Architecture & Directory Structure

```
fitbuddy/
│
├── app/
│   ├── main.py                     # FastAPI application setup, static mounting, lifespans & error handlers
│   ├── database.py                 # SQLAlchemy engine, session maker, get_db dependency
│   ├── models.py                   # Database entities: User, WorkoutPlan, PlanVersion, Feedback, NutritionGuide
│   ├── schemas.py                  # Pydantic v2 validation schemas with strict boundary constraints
│   ├── crud.py                     # Database transaction and querying operations
│   │
│   ├── services/
│   │   ├── gemini_service.py       # Google Gemini SDK integration, JSON cleanup, intelligent fallback
│   │   ├── workout_service.py      # Workout plan generation, validation, and feedback adaptation
│   │   └── nutrition_service.py    # Nutrition, hydration, and sleep guidance generator
│   │
│   ├── routers/
│   │   ├── users.py                # Profile viewing and registration routes
│   │   ├── workouts.py             # Workout generation, day-by-day views, feedback loop, history
│   │   ├── nutrition.py            # Nutrition and recovery assistant routes
│   │   └── admin.py                # Admin dashboard, metrics, and demo profile seeder
│   │
│   ├── templates/
│   │   ├── base.html               # Master layout, navigation, disclaimer banner, footer, AI modal
│   │   ├── index.html              # Landing page with hero, statistics, feature grid, active workout card
│   │   ├── profile.html            # Profile creation and editing form with limitation handling
│   │   ├── workout.html            # 7-day day-by-day cards, exercise checklists, rest timers, version picker
│   │   ├── nutrition.html          # Calorie and macro breakdown, meal timing, hydration, sleep protocols
│   │   ├── feedback.html           # Plan improvement form with quick-chips and adaptation triggers
│   │   ├── history.html            # Version timeline and historical workout inspector
│   │   └── admin.html              # System telemetry, metrics, user lists, plan inspector
│   │
│   └── static/
│       ├── css/
│       │   └── style.css           # Athletic dark theme, glassmorphic cards, animations, responsive rules
│       └── js/
│           └── app.js              # Rest countdown timer, checklist progress, AI loading animation
│
├── .env                            # Active environment variables (git-ignored)
├── .env.example                    # Environment template with documentation
├── .gitignore                      # Git exclusion rules
├── requirements.txt                # Complete pip dependencies
├── test_fitbuddy.py                # Automated test suite (7 comprehensive test suites)
├── README.md                       # Comprehensive documentation
└── run.py                          # Application startup entry point
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- Git (optional, for cloning).

### 2. Clone or Navigate to Project
```bash
cd path/to/fitbuddy
```

### 3. Create & Activate Virtual Environment
**Windows (PowerShell / Command Prompt):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration & Gemini API Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *(On Windows Command Prompt: `copy .env.example .env`)*

2. Open `.env` and configure your settings:
   ```env
   # Google Gemini API Key from Google AI Studio: https://aistudio.google.com/
   GEMINI_API_KEY=your_actual_gemini_api_key_here

   # Configurable Models (Prevents obsolescence as model names evolve)
   GEMINI_WORKOUT_MODEL=gemini-1.5-pro
   GEMINI_FAST_MODEL=gemini-1.5-flash

   # Database URL
   DATABASE_URL=sqlite:///./fitbuddy.db

   # Server Network Settings
   APP_HOST=127.0.0.1
   APP_PORT=8000
   DEBUG=True

   # Admin Dashboard Protection Key
   ADMIN_SECRET_KEY=fitbuddy-admin-secret-2025
   ```

> **Note on Offline / Keyless Mode**: If `GEMINI_API_KEY` is not provided, FitBuddy automatically engages its built-in intelligent exercise science engine. It generates fully structured, conservative 7-day fitness plans and macronutrient distributions so you can immediately explore and test the entire platform end-to-end without being blocked!

---

## 🏃 Running the Application

### Option A: Using the Launcher Script (Recommended)
```bash
python run.py
```

### Option B: Using Uvicorn Directly
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Accessing in Your Browser
Open your browser and navigate to:
- **Application Web UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Admin Dashboard**: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

## 🧪 Testing

The repository contains an automated test suite verifying:
- Pydantic schema validation boundaries (age, weight, height limits).
- Database CRUD operations and relational cascades.
- 7-Day workout plan generation and schema completeness.
- User feedback adaptation loop and Version archiving (`v1 → v2`).
- Nutrition and recovery guidance generation.
- FastAPI web route status codes and redirection flows.
- JSON REST API endpoints (`/api/users`, `/api/workouts/generate`, `/api/feedback`).

Run tests using either:
```bash
python test_fitbuddy.py
```
or with pytest:
```bash
pytest -v test_fitbuddy.py
```

---

## 📱 User Workflow

```
   1. Open FitBuddy (http://127.0.0.1:8000)
             │
             ▼
   2. Create / Edit Profile (/profile)
      • Age, Weight, Height, Target Goal
      • Training Level, Equipment, Limitations
             │
             ▼
   3. AI Generates 7-Day Plan (/workout)
      • Day 1 to Day 7 structured schedule
      • Interactive sets/reps & countdown rest timers
      • Dynamic warm-up and cool-down protocols
             │
             ▼
   4. View Nutrition Guidance (/nutrition)
      • Daily calorie baseline, protein/carb/fat macro split
      • Pre/post-workout meal timing, hydration target, sleep protocol
             │
             ▼
   5. Submit Feedback (/feedback)
      • Click quick chips or enter custom critique
      • Gemini adapts the plan into Version 2
             │
             ▼
   6. Inspect History (/history)
      • View timeline evolution from v1 to vN
```

---

## 🛡️ Health & Safety Guidelines

FitBuddy is an artificial intelligence-assisted fitness planning platform, **not a healthcare provider or emergency diagnostic system**.
- FitBuddy does not diagnose, treat, or cure medical conditions.
- Exercises are tailored conservatively based on user inputs.
- Individuals who are pregnant, recovering from surgery, or suffering from acute orthopedic, metabolic, or cardiovascular conditions must seek clearance from a qualified healthcare professional before beginning training.

---

## 🔧 Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `GEMINI_API_KEY is not configured` | Empty API key in `.env` | FitBuddy will automatically use the built-in intelligent engine. To enable live Gemini calls, add your key from [Google AI Studio](https://aistudio.google.com/) into `.env`. |
| Port 8000 already in use | Another process is bound to 8000 | In `.env`, change `APP_PORT=8001` or terminate the existing process. |
| Model not found error | Older model retired by Google | Change `GEMINI_WORKOUT_MODEL` or `GEMINI_FAST_MODEL` in `.env` to the newest available model identifier (e.g. `gemini-2.5-flash` or `gemini-1.5-pro`). |

---

## 🔮 Future Enhancements

- Wearable device sync (Apple HealthKit / Google Health Connect).
- Exercise video demonstration animations.
- Barcode scanner for nutrition macro logging.
- Multi-user authentication with OAuth2 / Google Sign-In.

---

## 📄 License

MIT License. Built for health, fitness, and longevity.
