from apscheduler.schedulers.background import BackgroundScheduler
from tasks.jobs import check_negative_balances
import os

scheduler = BackgroundScheduler()

# Add a job that runs every hour
scheduler.add_job(check_negative_balances, "interval", hours=1)

# Only start scheduler if it's the main process (avoids running twice with uvicorn --reload)
if os.getenv("RUN_MAIN") == "true" or os.getenv("ENV") == "production":
    scheduler.start()
