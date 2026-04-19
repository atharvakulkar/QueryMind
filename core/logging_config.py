"""Central logging setup (console only; never stdout in MCP — use stderr via logging)."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once for the process."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(numeric)
        return

    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stderr)],
    )
