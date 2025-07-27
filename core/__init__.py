# Gold Digger AI Bot - Core Module
# Contains the main trading logic, indicators, and integrations

__version__ = "1.0.0"
__author__ = "Gold Digger AI Team"

# Core module imports
from .mt5_connector import MT5Connector
from .gemini_client import GeminiClient
from .indicators import SMCIndicators
from .trading_engine import TradingEngine
from .risk_manager import RiskManager

__all__ = [
    "MT5Connector",
    "GeminiClient", 
    "SMCIndicators",
    "TradingEngine",
    "RiskManager"
]
