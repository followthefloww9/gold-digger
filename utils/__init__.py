# Gold Digger AI Bot - Utilities Module
# Contains helper functions, data management, and notification systems

__version__ = "1.0.0"

from .data_manager import DataManager
from .logger import setup_logger
from .notifications import NotificationManager

__all__ = [
    "DataManager",
    "setup_logger",
    "NotificationManager"
]
