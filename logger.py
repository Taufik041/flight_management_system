import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory
LOG_DIR = "logs"
LOG_FILE = "app.log"
os.makedirs(LOG_DIR, exist_ok=True)

# File log format
file_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler (rotating)
file_handler = RotatingFileHandler(
    filename=os.path.join(LOG_DIR, LOG_FILE),
    maxBytes=5 * 1024 * 1024,
    backupCount=3
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

# Main logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Prevent adding multiple handlers
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    logger.addHandler(file_handler)