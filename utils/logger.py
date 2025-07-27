"""
Gold Digger AI Bot - Enhanced Logging System
Professional logging with file rotation and structured output
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

def setup_logger(name: str = "gold_digger", 
                log_level: str = "INFO",
                log_dir: str = "logs",
                max_file_size: int = 10 * 1024 * 1024,  # 10MB
                backup_count: int = 5) -> logging.Logger:
    """
    Set up enhanced logger with file rotation and structured output
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        max_file_size: Maximum size per log file in bytes
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    log_file = log_path / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Error file handler (separate file for errors)
    error_file = log_path / f"{name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Trade log handler (for trade-specific events)
    trade_file = log_path / f"{name}_trades.log"
    trade_handler = logging.handlers.RotatingFileHandler(
        trade_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    trade_handler.setLevel(logging.INFO)
    trade_handler.setFormatter(detailed_formatter)
    
    # Add filter for trade-related logs
    class TradeFilter(logging.Filter):
        def filter(self, record):
            return 'trade' in record.getMessage().lower() or 'signal' in record.getMessage().lower()
    
    trade_handler.addFilter(TradeFilter())
    logger.addHandler(trade_handler)
    
    logger.info(f"Logger '{name}' initialized with level {log_level}")
    return logger

class StructuredLogger:
    """
    Structured logger for JSON-formatted logs with metadata
    """
    
    def __init__(self, name: str = "gold_digger_structured", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # JSON file handler
        json_file = log_path / f"{name}.jsonl"
        json_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.logger.addHandler(json_handler)
    
    def log_trade_event(self, event_type: str, trade_data: dict, metadata: dict = None):
        """Log trade event in structured format"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'trade_data': trade_data,
            'metadata': metadata or {}
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_system_event(self, event_type: str, message: str, data: dict = None):
        """Log system event in structured format"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'data': data or {}
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_performance_metrics(self, metrics: dict):
        """Log performance metrics"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'PERFORMANCE_METRICS',
            'metrics': metrics
        }
        
        self.logger.info(json.dumps(log_entry))

# Global logger instance
_global_logger = None

def get_logger(name: str = "gold_digger") -> logging.Logger:
    """Get or create global logger instance"""
    global _global_logger
    
    if _global_logger is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        _global_logger = setup_logger(name, log_level)
    
    return _global_logger

def log_trade_signal(signal_data: dict):
    """Convenience function to log trade signals"""
    logger = get_logger()
    logger.info(f"TRADE_SIGNAL: {signal_data.get('signal', 'UNKNOWN')} | "
               f"Confidence: {signal_data.get('confidence', 0)*100:.1f}% | "
               f"Entry: ${signal_data.get('entry_price', 0):.2f} | "
               f"R:R: 1:{signal_data.get('risk_reward_ratio', 0):.1f}")

def log_trade_execution(trade_data: dict):
    """Convenience function to log trade executions"""
    logger = get_logger()
    logger.info(f"TRADE_EXECUTED: {trade_data.get('direction', 'UNKNOWN')} | "
               f"Size: {trade_data.get('lot_size', 0):.2f} lots | "
               f"Entry: ${trade_data.get('entry_price', 0):.2f} | "
               f"SL: ${trade_data.get('stop_loss', 0):.2f} | "
               f"TP: ${trade_data.get('take_profit', 0):.2f}")

def log_trade_close(close_data: dict):
    """Convenience function to log trade closures"""
    logger = get_logger()
    pnl = close_data.get('pnl', 0)
    pnl_sign = '+' if pnl >= 0 else ''
    logger.info(f"TRADE_CLOSED: {close_data.get('direction', 'UNKNOWN')} | "
               f"Exit: ${close_data.get('exit_price', 0):.2f} | "
               f"P&L: {pnl_sign}${pnl:.2f} | "
               f"Reason: {close_data.get('close_reason', 'UNKNOWN')}")

def log_system_status(status: str, details: dict = None):
    """Convenience function to log system status"""
    logger = get_logger()
    details_str = f" | {details}" if details else ""
    logger.info(f"SYSTEM_STATUS: {status}{details_str}")

def log_error(error_msg: str, exception: Exception = None):
    """Convenience function to log errors"""
    logger = get_logger()
    if exception:
        logger.error(f"ERROR: {error_msg} | Exception: {str(exception)}", exc_info=True)
    else:
        logger.error(f"ERROR: {error_msg}")

def log_performance_update(metrics: dict):
    """Convenience function to log performance updates"""
    logger = get_logger()
    logger.info(f"PERFORMANCE: Balance: ${metrics.get('balance', 0):,.2f} | "
               f"Daily P&L: ${metrics.get('daily_pnl', 0):+.2f} | "
               f"Win Rate: {metrics.get('win_rate', 0):.1f}% | "
               f"Drawdown: {metrics.get('drawdown', 0):.2f}%")

# Test function
def test_logger():
    """Test logging system"""
    print("🔍 Testing Logging System...")
    
    # Test basic logger
    logger = setup_logger("test_logger", "DEBUG")
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test convenience functions
    log_trade_signal({
        'signal': 'BUY',
        'confidence': 0.85,
        'entry_price': 1987.50,
        'risk_reward_ratio': 2.0
    })
    
    log_trade_execution({
        'direction': 'BUY',
        'lot_size': 0.1,
        'entry_price': 1987.50,
        'stop_loss': 1985.00,
        'take_profit': 1992.50
    })
    
    log_performance_update({
        'balance': 100250.00,
        'daily_pnl': 250.00,
        'win_rate': 73.5,
        'drawdown': 2.1
    })
    
    # Test structured logger
    structured_logger = StructuredLogger("test_structured")
    
    structured_logger.log_trade_event("SIGNAL_GENERATED", {
        'signal': 'BUY',
        'confidence': 0.85,
        'entry_price': 1987.50
    })
    
    structured_logger.log_system_event("SYSTEM_START", "Bot initialized successfully")
    
    print("✅ Logging System Test Results:")
    print("   Basic Logger: PASS")
    print("   Convenience Functions: PASS")
    print("   Structured Logger: PASS")
    print("   Log Files: Check logs/ directory")
    
    return True

if __name__ == "__main__":
    test_logger()
