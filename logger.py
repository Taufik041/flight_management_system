import logging
import sys

# Create a custom logger
logger = logging.getLogger("flight_management_system")
logger.setLevel(logging.DEBUG)  # Log everything

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("logs/app.log")
file_handler.setLevel(logging.DEBUG)

# Create formatters and add them to handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger (avoid duplicate handlers)
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler) 