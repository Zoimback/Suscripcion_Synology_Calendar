"""pytest configuration — adds repo root to sys.path so tests can import ics_sync."""
import sys
from pathlib import Path

# Ensure the repo root is on the path so `from ics_sync import ...` works without
# installing the package in editable mode.
sys.path.insert(0, str(Path(__file__).parent))
