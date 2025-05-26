# File: app/core/logger.py
from loguru import logger
import sys

# Remove default handlers and add custom configuration
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{module}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
