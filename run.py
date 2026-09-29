import os
import sys
import uvicorn
from dotenv import load_dotenv

# Ensure utf-8 output encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment configuration
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    reload = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    print(f"FitBuddy AI Platform starting on http://{host}:{port}")
    print(f"Interactive Swagger Documentation: http://{host}:{port}/docs")
    print(f"Press CTRL+C to terminate.")

    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
