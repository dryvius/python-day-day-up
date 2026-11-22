"""Logging configuration shared by CLI entry points."""

import logging


def configure_logging(verbose: bool) -> None:
    """Configure predictable command-line logging."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
        force=True,
    )
