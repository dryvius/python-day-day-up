"""Logging configuration with conservative secret redaction."""

import logging
import re

SECRET_PATTERN = re.compile(r"(?:sk-[A-Za-z0-9_-]{6,}|Bearer\s+\S+)")


class SecretRedactionFilter(logging.Filter):
    """Redact common provider credentials from rendered log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        rendered = record.getMessage()
        record.msg = SECRET_PATTERN.sub("[REDACTED]", rendered)
        record.args = ()
        return True


def configure_logging() -> None:
    """Install one redacting handler on the project logger."""

    logger = logging.getLogger("ai_chat")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.addFilter(SecretRedactionFilter())
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
