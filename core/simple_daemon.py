"""
Gold Digger AI Bot - Simple Thread-Based Daemon
Simpler implementation using threading for better compatibility
"""

import os
import sys
import time
import threading
import json
from datetime import datetime
from typing import Dict, Tuple
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.live_trading_engine import LiveTradingEngine
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger("simple_daemon")

class SimpleDaemon:
    """
    Simple thread-based daemon for background trading
    More compatible than multiprocessing approach
    """
    
    def __init__(self):
        self.engine = None
        self.data_manager = DataManager()
        self.running = False
        self.daemon_thread = None
        self.status_file = "simple_daemon_status.json"
        
        logger.info("Simple Daemon initialized")
    
    def start_trading(self, paper_trading: bool = True, 
                     risk_percentage: float = 1.0, 
                     max_risk_amount: float = 1000.0) -> Tuple[bool, str]:
        """
        Start background trading
        
        Args:
            paper_trading: Whether to use paper trading
            risk_percentage: Risk percentage per trade
            max_risk_amount: Maximum risk amount per trade
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.running:
                return False, "Daemon already running"
            
            # Initialize trading engine
            self.engine = LiveTradingEngine(paper_trading=paper_trading)
            
            # Configure risk settings
            self.engine.risk_manager.risk_percentage = risk_percentage
            self.engine.risk_manager.max_risk_amount = max_risk_amount
            
            # Start trading engine
            if not self.engine.start_trading():
                return False, "Failed to start trading engine"
            
            # Start daemon thread
            self.running = True
            self.daemon_thread = threading.Thread(
                target=self._daemon_loop,
                args=(paper_trading, risk_percentage, max_risk_amount),
                daemon=True
            )
            self.daemon_thread.start()
            
            # Update database state
            self.data_manager.save_bot_state(
                is_running=True,
                trading_mode='Paper Trading' if paper_trading else 'Live Trading',
                risk_percentage=risk_percentage,
                max_risk_amount=max_risk_amount,
                session_id='simple_daemon',
                configuration={
                    'daemon_type': 'simple_thread',
                    'start_time': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Simple daemon started - Paper Trading: {paper_trading}")
            mode = "Paper Trading" if paper_trading else "Live Trading"
            return True, f"Background trading started in {mode} mode"
            
        except Exception as e:
            logger.error(f"Failed to start simple daemon: {e}")
            return False, f"Error: {str(e)}"
    
    def stop_trading(self) -> Tuple[bool, str]:
        """
        Stop background trading
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.running:
                return False, "Daemon not running"
            
            # Stop daemon loop
            self.running = False
            
            # Stop trading engine
            if self.engine:
                self.engine.stop_trading()
                self.engine = None
            
            # Wait for thread to finish
            if self.daemon_thread and self.daemon_thread.is_alive():
                self.daemon_thread.join(timeout=5)
            
            # Update database state
            self.data_manager.save_bot_state(
                is_running=False,
                trading_mode='Paper Trading',
                risk_percentage=1.0,
                max_risk_amount=1000.0,
                session_id='simple_daemon',
                configuration={'stop_time': datetime.now().isoformat()}
            )
            
            # Clean up status file
            if os.path.exists(self.status_file):
                os.remove(self.status_file)
            
            logger.info("Simple daemon stopped")
            return True, "Background trading stopped successfully"
            
        except Exception as e:
            logger.error(f"Error stopping simple daemon: {e}")
            return False, f"Error: {str(e)}"
    
    def get_status(self) -> Dict:
        """
        Get daemon status
        
        Returns:
            Dictionary with status information
        """
        try:
            status = {
                'running': self.running,
                'thread_alive': self.daemon_thread.is_alive() if self.daemon_thread else False,
                'engine_running': self.engine.is_running if self.engine else False,
                'trades_today': self.engine.daily_trade_count if self.engine else 0,
                'open_positions': len(self.engine.open_positions) if self.engine else 0,
                'last_update': datetime.now().isoformat()
            }
            
            # Read status file if exists
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    file_status = json.load(f)
                    status.update(file_status)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting daemon status: {e}")
            return {
                'running': False,
                'error': str(e),
                'last_update': datetime.now().isoformat()
            }
    
    def _daemon_loop(self, paper_trading: bool, risk_percentage: float, max_risk_amount: float):
        """
        Main daemon loop running in background thread
        
        Args:
            paper_trading: Whether using paper trading
            risk_percentage: Risk percentage per trade
            max_risk_amount: Maximum risk amount per trade
        """
        try:
            logger.info("Simple daemon loop started")
            start_time = datetime.now()
            
            while self.running:
                try:
                    # Check if we should still be running (from database)
                    bot_state = self.data_manager.get_bot_state()
                    if not bot_state.get('is_running', False):
                        logger.info("Bot stopped via database - shutting down daemon")
                        break
                    
                    # Update status file
                    status = {
                        'last_heartbeat': datetime.now().isoformat(),
                        'uptime': str(datetime.now() - start_time),
                        'trades_today': self.engine.daily_trade_count if self.engine else 0,
                        'open_positions': len(self.engine.open_positions) if self.engine else 0,
                        'paper_trading': paper_trading,
                        'risk_percentage': risk_percentage,
                        'max_risk_amount': max_risk_amount,
                        'engine_status': 'running' if (self.engine and self.engine.is_running) else 'stopped'
                    }
                    
                    with open(self.status_file, 'w') as f:
                        json.dump(status, f, indent=2)
                    
                    # Sleep for heartbeat interval
                    time.sleep(30)  # 30 second heartbeat
                    
                except Exception as e:
                    logger.error(f"Error in daemon loop: {e}")
                    time.sleep(5)  # Brief pause before retrying
            
            logger.info("Simple daemon loop ended")
            
        except Exception as e:
            logger.error(f"Fatal error in daemon loop: {e}")
        finally:
            # Clean up
            if os.path.exists(self.status_file):
                os.remove(self.status_file)


# Global instance
simple_daemon = SimpleDaemon()


def test_simple_daemon():
    """Test the simple daemon"""
    print("🔍 Testing Simple Daemon")
    print("=" * 30)
    
    try:
        # Test start
        success, message = simple_daemon.start_trading(
            paper_trading=True,
            risk_percentage=1.0,
            max_risk_amount=500.0
        )
        print(f"Start: {success} - {message}")
        
        if success:
            # Wait and check status
            time.sleep(3)
            status = simple_daemon.get_status()
            print(f"Status: {status}")
            
            # Test stop
            success, message = simple_daemon.stop_trading()
            print(f"Stop: {success} - {message}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple_daemon()
