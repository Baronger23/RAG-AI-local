"""
Logging setup for GeekBrain W4 system
Supports JSON logging and regular structured logging
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from config import LOG_FILE, LOG_JSON, LOG_LEVEL


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with both file and console handlers"""

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    if LOG_JSON:
        console_formatter = JSONFormatter()
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))

        if LOG_JSON:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file handler: {e}")

    return logger


def log_tool_call(
    logger: logging.Logger,
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Dict[str, Any],
    duration_ms: float,
) -> None:
    """Log a tool invocation with input/output"""

    logger.info(
        f"Tool call: {tool_name}",
        extra={
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output,
            "duration_ms": duration_ms,
        },
    )


# Main logger
logger = setup_logger("geekbrain")
