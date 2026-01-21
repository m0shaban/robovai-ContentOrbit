# ContentOrbit Enterprise - Core Engine
# The heart of the content automation system

__version__ = "1.0.0"
__author__ = "ContentOrbit Team"

from .config_manager import ConfigManager, get_config, reload_config
from .database_manager import DatabaseManager, get_db, close_db

# Keep heavy imports optional so lightweight consumers (e.g. image generator demo)
# don't require the full pipeline dependencies at import-time.
try:
    from .content_orchestrator import ContentOrchestrator, PipelineResult
except Exception:  # pragma: no cover
    ContentOrchestrator = None  # type: ignore[assignment]
    PipelineResult = None  # type: ignore[assignment]

__all__ = [
    "ConfigManager",
    "get_config",
    "reload_config",
    "DatabaseManager",
    "get_db",
    "close_db",
]

if ContentOrchestrator is not None:
    __all__ += [
        "ContentOrchestrator",
        "PipelineResult",
    ]
