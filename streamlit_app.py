"""Legacy Streamlit entrypoint.

Some Streamlit deployments are configured to run `streamlit_app.py` by default.
This file is kept as a compatibility shim and delegates to the real dashboard:
`dashboard/main_dashboard.py`.

Preferred entrypoint: `main_dashboard.py` or `dashboard/main_dashboard.py`.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Importing this module runs the Streamlit dashboard.
from dashboard import main_dashboard as _main_dashboard  # noqa: F401
