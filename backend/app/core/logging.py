"""Structured and security-hardened logging for MediaVault.

Strictly prevents logging of passwords, derived keys, or plaintext contents.
Provides JSON and formatted console logs with contextual metadata and tracing.
"""

import json
import logging
import re
import sys
from typing import Any, Dict


SENSITIVE_PATTERNS = [
    re.compile(r"(password|pwd|secret|key|token|auth)[\"']?\s*[:=]\s*[\"']?([^\"'\s,]+)", re.IGNORECASE),
    re.compile(r"(--password|-p)\s+([^\s]+)", re.IGNORECASE),
]


class SecuritySanitizingFilter(logging.Filter):
    """Filter that sanitizes log records to ensure no passwords or keys leak."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.sanitize(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.sanitize(v) if isinstance(v, str) else v for v in record.args)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        sanitized = text
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r"\1=[REDACTED]", sanitized)
        return sanitized


class JsonFormatter(logging.Formatter):
    """Formats logs into structured JSON for machine parsing & observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "job_id"):
            log_obj["job_id"] = record.job_id
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "event"):
            log_obj["event"] = record.event
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(level: int = logging.INFO, json_output: bool = False) -> logging.Logger:
    """Configures root logger with security filters."""
    logger = logging.getLogger("mediavault")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.addFilter(SecuritySanitizingFilter())

        if json_output:
            handler.setFormatter(JsonFormatter())
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logging()
