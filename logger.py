import logging
import sys
import re
from datetime import datetime

# Create a custom logger
logger = logging.getLogger("flight_management_system")
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("logs/app.log")
file_handler.setLevel(logging.DEBUG)

# Endpoint description mapping
endpoint_map = {
    'GET / HTTP/1.1': 'Root endpoint accessed',
    'GET /favicon.ico HTTP/1.1': 'Favicon endpoint accessed',
    'GET /one HTTP/1.1': 'One endpoint accessed',
}

# Custom formatter for access logs (for file only)
class AccessLogFormatter(logging.Formatter):
    def format(self, record):
        if record.args:
            message = record.getMessage()
        else:
            message = record.msg
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        formatted_message = f"{timestamp} - {message}"
        record.msg = formatted_message
        record.args = ()
        return formatted_message

# Create formatters
standard_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
access_file_formatter = AccessLogFormatter()

# Add handlers to main logger
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    console_handler.setFormatter(standard_formatter)
    file_handler.setFormatter(standard_formatter)

# Configure uvicorn access logger
uvicorn_access_logger = logging.getLogger("uvicorn.access")
# Remove only file handlers, keep console handlers untouched
uvicorn_access_logger.handlers = [
    h for h in uvicorn_access_logger.handlers
    if not isinstance(h, logging.FileHandler)
]
uvicorn_access_logger.setLevel(logging.INFO)

# Only add a file handler to uvicorn.access, leave console alone for pretty output
access_file_handler = logging.FileHandler("logs/app.log")
access_file_handler.setLevel(logging.INFO)
access_file_handler.setFormatter(AccessLogFormatter())

uvicorn_access_logger.addHandler(access_file_handler) 