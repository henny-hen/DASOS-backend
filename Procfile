# Procfile (for Railway)
web: python rest-api.py --host 0.0.0.0 --port $PORT

# railway.toml (optional configuration)
[build]
  builder = "nixpacks"

[deploy]
  healthcheckPath = "/health"
  healthcheckTimeout = 300
  restartPolicyType = "never"

# .env (for local development - don't commit this)
FLASK_ENV=development
DATABASE_PATH=academic_data.db
PORT=8000