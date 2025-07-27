# Gold Digger AI Bot - Backtesting Module
# Historical strategy testing and optimization

__version__ = "1.0.0"

from .backtester import BacktestEngine
from .optimizer import StrategyOptimizer

__all__ = [
    "BacktestEngine",
    "StrategyOptimizer"
]
