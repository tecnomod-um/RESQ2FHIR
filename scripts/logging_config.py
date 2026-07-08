"""
Logging configuration for RESQ2FHIR.
Configures structured logging with console and file handlers.
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime


def setup_logging(log_level=None):
    """
    Configure logging for the application.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to DEBUG if RESQ_LOG_LEVEL not set, otherwise uses env var.
    
    Creates logs in: ./logs/resq2fhir.log
    """
    # Get log level from environment or default to DEBUG
    if log_level is None:
        log_level = os.getenv("RESQ_LOG_LEVEL", "DEBUG").upper()
    
    log_file = Path(os.getenv("RESQ_LOG_FILE", "logs/resq2fhir.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Format for logs
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str):
    """
    Get a logger for a specific module.
    
    Usage:
        from scripts.logging_config import get_logger
        logger = get_logger(__name__)
        logger.debug("Debug message")
        logger.info("Info message")
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)


# Redirect print statements to logging
class PrintLogger:
    """Redirects print() calls to logger."""
    
    def __init__(self, logger: logging.Logger, level=logging.INFO):
        self.logger = logger
        self.level = level
    
    def write(self, message: str):
        if message.strip():  # Ignore empty lines
            self.logger.log(self.level, message.strip())
    
    def flush(self):
        pass


def redirect_prints_to_logging():
    """
    Redirect stdout to logging so print() statements appear in logs.
    Call this in your main script.
    """
    logger = logging.getLogger("__print__")
    sys.stdout = PrintLogger(logger, logging.INFO)
