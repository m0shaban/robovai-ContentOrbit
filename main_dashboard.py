"""ContentOrbit Enterprise - Streamlit entrypoint.

Streamlit Community Cloud is configured to run this file.
It delegates to the real dashboard app in `dashboard/main_dashboard.py`.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Importing this module runs the Streamlit dashboard.
from dashboard import main_dashboard as _main_dashboard  # noqa: F401
