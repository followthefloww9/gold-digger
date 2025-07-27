"""
Gold Digger AI Bot - Trading Daemon
Independent background service for continuous trading
"""

import os
import sys
import time
import signal
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import json
import psutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.live_trading_engine import LiveTradingEngine
from utils.data_manager import DataManager
from utils.logger import get_logger

# Set up logging
logger = get_logger("trading_daemon")

class TradingDaemon:
    """
    Independent trading daemon that runs as a background process
    Continues trading even when UI is disconnected
    """
    
    def __init__(self):
        self.daemon_pid = None
        self.engine = None
        self.data_manager = DataManager()
        self.running = False
        self.heartbeat_interval = 30  # seconds
        self.last_heartbeat = None
        
        # Daemon control files
        self.pid_file = "trading_daemon.pid"
        self.status_file = "daemon_status.json"
        self.log_file = "daemon.log"
        
        # Set up signal handlers (only in main thread)
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # Signal handlers can only be set in main thread
            # This is expected when running from Streamlit
            pass
        
        logger.info("Trading Daemon initialized")
    
    def start_daemon(self, paper_trading: bool = True, risk_percentage: float = 1.0, 
                    max_risk_amount: float = 1000.0) -> bool:
        """
        Start the trading daemon as a background process
        
        Args:
            paper_trading: Whether to use paper trading
            risk_percentage: Risk percentage per trade
            max_risk_amount: Maximum risk amount per trade
            
        Returns:
            True if daemon started successfully
        """
        try:
            # Check if daemon is already running
            if self.is_daemon_running():
                logger.warning("Trading daemon already running")
                return False
            
            # Create daemon process
            daemon_process = multiprocessing.Process(
                target=self._daemon_main_loop,
                args=(paper_trading, risk_percentage, max_risk_amount),
                daemon=False  # Don't make it a daemon process so it can run independently
            )

            daemon_process.start()
            self.daemon_pid = daemon_process.pid

            # Wait a moment to see if process starts successfully
            import time
            time.sleep(1)

            # Check if process is still alive
            if not daemon_process.is_alive():
                logger.error("Daemon process died immediately after start")
                return False

            # Save PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(self.daemon_pid))

            # Wait a bit more and verify process is still running
            time.sleep(1)
            if not daemon_process.is_alive():
                logger.error("Daemon process died after PID file creation")
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
                return False
            
            # Update database state
            self.data_manager.save_bot_state(
                is_running=True,
                trading_mode='Paper Trading' if paper_trading else 'Live Trading',
                risk_percentage=risk_percentage,
                max_risk_amount=max_risk_amount,
                session_id='daemon',
                configuration={
                    'daemon_pid': self.daemon_pid,
                    'daemon_start_time': datetime.now().isoformat(),
                    'background_service': True
                }
            )
            
            logger.info(f"Trading daemon started with PID: {self.daemon_pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trading daemon: {e}")
            return False
    
    def stop_daemon(self) -> bool:
        """
        Stop the trading daemon
        
        Returns:
            True if daemon stopped successfully
        """
        try:
            if not self.is_daemon_running():
                logger.warning("Trading daemon not running")
                return False
            
            # Get PID from file
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Terminate the process
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    process.wait(timeout=10)
                    
                except psutil.NoSuchProcess:
                    logger.warning(f"Process {pid} not found")
                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    process.kill()
                    logger.warning(f"Force killed daemon process {pid}")
                
                # Clean up files
                os.remove(self.pid_file)
                if os.path.exists(self.status_file):
                    os.remove(self.status_file)
            
            # Update database state
            self.data_manager.save_bot_state(
                is_running=False,
                trading_mode='Paper Trading',
                risk_percentage=1.0,
                max_risk_amount=1000.0,
                session_id='daemon',
                configuration={'daemon_stopped': datetime.now().isoformat()}
            )
            
            logger.info("Trading daemon stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop trading daemon: {e}")
            return False
    
    def is_daemon_running(self) -> bool:
        """
        Check if trading daemon is currently running
        
        Returns:
            True if daemon is running
        """
        try:
            if not os.path.exists(self.pid_file):
                return False
            
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists and is our daemon
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    # Check if it's actually our trading daemon
                    cmdline = ' '.join(process.cmdline())
                    if 'trading_daemon' in cmdline or 'daemon_main_loop' in cmdline:
                        return True
            except psutil.NoSuchProcess:
                pass
            
            # Clean up stale PID file
            os.remove(self.pid_file)
            return False
            
        except Exception as e:
            logger.error(f"Error checking daemon status: {e}")
            return False
    
    def get_daemon_status(self) -> Dict:
        """
        Get current daemon status
        
        Returns:
            Dictionary with daemon status information
        """
        try:
            if not self.is_daemon_running():
                return {
                    'running': False,
                    'pid': None,
                    'uptime': None,
                    'last_heartbeat': None,
                    'trades_today': 0,
                    'open_positions': 0
                }
            
            # Read status file if it exists
            status = {
                'running': True,
                'pid': None,
                'uptime': None,
                'last_heartbeat': None,
                'trades_today': 0,
                'open_positions': 0
            }
            
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    status['pid'] = int(f.read().strip())
            
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    file_status = json.load(f)
                    status.update(file_status)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting daemon status: {e}")
            return {'running': False, 'error': str(e)}
    
    def _daemon_main_loop(self, paper_trading: bool, risk_percentage: float, max_risk_amount: float):
        """
        Main daemon loop - runs in separate process

        Args:
            paper_trading: Whether to use paper trading
            risk_percentage: Risk percentage per trade
            max_risk_amount: Maximum risk amount per trade
        """
        try:
            # Ensure proper module path for daemon process
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # Set up logging for daemon process
            daemon_logger = get_logger("daemon_process")
            daemon_logger.info(f"Daemon process started - PID: {os.getpid()}")

            # Re-import in daemon process context
            from core.live_trading_engine import LiveTradingEngine
            from utils.data_manager import DataManager

            # Initialize components
            self.data_manager = DataManager()
            self.engine = LiveTradingEngine(paper_trading=paper_trading)
            
            # Configure risk settings
            self.engine.risk_manager.risk_percentage = risk_percentage
            self.engine.risk_manager.max_risk_amount = max_risk_amount
            
            # Start trading engine
            daemon_logger.info("Starting trading engine...")
            if not self.engine.start_trading():
                daemon_logger.error("Failed to start trading engine in daemon")
                # Write error for debugging
                with open("daemon_startup_error.log", "w") as f:
                    f.write("Failed to start trading engine in daemon process")
                return
            
            self.running = True
            start_time = datetime.now()

            # Write startup success indicator
            with open("daemon_startup_success.log", "w") as f:
                f.write(f"Daemon started successfully - PID: {os.getpid()}")

            daemon_logger.info("Daemon trading loop started")
            
            # Main daemon loop
            while self.running:
                try:
                    # Update heartbeat
                    self.last_heartbeat = datetime.now()
                    
                    # Check if we should still be running (from database)
                    bot_state = self.data_manager.get_bot_state()
                    if not bot_state.get('is_running', False):
                        daemon_logger.info("Bot stopped via database - shutting down daemon")
                        break
                    
                    # Update status file
                    status = {
                        'last_heartbeat': self.last_heartbeat.isoformat(),
                        'uptime': str(datetime.now() - start_time),
                        'trades_today': self.engine.daily_trade_count,
                        'open_positions': len(self.engine.open_positions),
                        'paper_trading': paper_trading,
                        'risk_percentage': risk_percentage,
                        'max_risk_amount': max_risk_amount
                    }
                    
                    with open(self.status_file, 'w') as f:
                        json.dump(status, f, indent=2)
                    
                    # Sleep for heartbeat interval
                    time.sleep(self.heartbeat_interval)
                    
                except Exception as e:
                    daemon_logger.error(f"Error in daemon loop: {e}")
                    time.sleep(5)  # Brief pause before retrying
            
            # Clean shutdown
            if self.engine:
                self.engine.stop_trading()
            
            daemon_logger.info("Daemon process shutting down")
            
        except Exception as e:
            daemon_logger.error(f"Fatal error in daemon process: {e}")
            # Write error to a file for debugging
            try:
                with open("daemon_error.log", "w") as f:
                    import traceback
                    f.write(f"Daemon error: {e}\n")
                    f.write(traceback.format_exc())
            except:
                pass
        finally:
            # Clean up
            if os.path.exists(self.status_file):
                os.remove(self.status_file)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        try:
            logger.info(f"Received signal {signum} - shutting down daemon")
            self.running = False
        except Exception as e:
            # Ensure we always set running to False
            self.running = False
            print(f"Signal handler error: {e}")


def main():
    """Main entry point for daemon"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gold Digger Trading Daemon')
    parser.add_argument('action', choices=['start', 'stop', 'status'], help='Daemon action')
    parser.add_argument('--paper', action='store_true', help='Use paper trading')
    parser.add_argument('--risk', type=float, default=1.0, help='Risk percentage')
    parser.add_argument('--max-risk', type=float, default=1000.0, help='Max risk amount')
    
    args = parser.parse_args()
    
    daemon = TradingDaemon()
    
    if args.action == 'start':
        success = daemon.start_daemon(args.paper, args.risk, args.max_risk)
        print(f"Daemon start: {'SUCCESS' if success else 'FAILED'}")
    elif args.action == 'stop':
        success = daemon.stop_daemon()
        print(f"Daemon stop: {'SUCCESS' if success else 'FAILED'}")
    elif args.action == 'status':
        status = daemon.get_daemon_status()
        print(f"Daemon status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    main()
