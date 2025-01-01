import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime
import structlog
from app.core.config import settings

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

def setup_logging() -> None:
    """Configure logging settings"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Basic configuration
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Set log levels for third-party packages
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

class CustomJSONFormatter(logging.Formatter):
    """Custom JSON formatter for logging"""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.default_keys = [
            "timestamp", "level", "message", "logger",
            "path", "method", "request_id"
        ]

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in self.default_keys and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data)

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance"""
    return structlog.get_logger(name)