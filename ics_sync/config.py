"""Configuration loading for ICS → CalDAV sync."""
import json
from pathlib import Path


def load_config(path: str | Path = "config.json") -> dict:
    """Load and return the JSON configuration dictionary from *path*."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
