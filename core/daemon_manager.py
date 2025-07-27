"""
Gold Digger AI Bot - Daemon Manager
Interface between Streamlit UI and background trading daemon
"""

import os
import time
import subprocess
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from pathlib import Path

from .simple_daemon import simple_daemon
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger("daemon_manager")

class DaemonManager:
    """
    Manages the background trading daemon from the Streamlit UI
    Provides seamless integration between UI and background service
    """

    def __init__(self):
        self.daemon = simple_daemon
        self.data_manager = DataManager()
        
    def start_background_trading(self, paper_trading: bool = True, 
                               risk_percentage: float = 1.0, 
                               max_risk_amount: float = 1000.0) -> Tuple[bool, str]:
        """
        Start background trading daemon
        
        Args:
            paper_trading: Whether to use paper trading
            risk_percentage: Risk percentage per trade
            max_risk_amount: Maximum risk amount per trade
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if daemon is already running
            if self.daemon.running:
                return False, "Trading daemon is already running"

            # Start the daemon
            success, message = self.daemon.start_trading(
                paper_trading=paper_trading,
                risk_percentage=risk_percentage,
                max_risk_amount=max_risk_amount
            )

            if success:
                # Wait a moment for daemon to initialize
                time.sleep(1)

                # Verify daemon started successfully
                status = self.daemon.get_status()
                if status.get('running', False):
                    return True, message
                else:
                    return False, "Daemon failed to start properly"
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error starting background trading: {e}")
            return False, f"Error: {str(e)}"
    
    def stop_background_trading(self) -> Tuple[bool, str]:
        """
        Stop background trading daemon
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.daemon.running:
                return False, "Trading daemon is not running"

            success, message = self.daemon.stop_trading()

            if success:
                return True, message
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error stopping background trading: {e}")
            return False, f"Error: {str(e)}"
    
    def get_trading_status(self) -> Dict:
        """
        Get comprehensive trading status including daemon and database state
        
        Returns:
            Dictionary with complete trading status
        """
        try:
            # Get daemon status
            daemon_status = self.daemon.get_status()

            # Get database state
            db_state = self.data_manager.get_bot_state()

            # Combine information
            status = {
                'daemon_running': daemon_status.get('running', False),
                'daemon_pid': 'thread',  # Thread-based, no PID
                'database_running': db_state.get('is_running', False),
                'trading_mode': db_state.get('trading_mode', 'Paper Trading'),
                'risk_percentage': db_state.get('risk_percentage', 1.0),
                'max_risk_amount': db_state.get('max_risk_amount', 1000.0),
                'last_heartbeat': daemon_status.get('last_heartbeat'),
                'uptime': daemon_status.get('uptime'),
                'trades_today': daemon_status.get('trades_today', 0),
                'open_positions': daemon_status.get('open_positions', 0),
                'last_database_update': db_state.get('last_updated'),
                'session_id': db_state.get('session_id'),
                'configuration': db_state.get('configuration', {})
            }
            
            # Determine overall status
            if status['daemon_running'] and status['database_running']:
                status['overall_status'] = 'ONLINE'
                status['status_message'] = 'Trading daemon active and running'
            elif status['database_running'] and not status['daemon_running']:
                status['overall_status'] = 'STARTING'
                status['status_message'] = 'Bot marked as running but daemon not active'
            elif status['daemon_running'] and not status['database_running']:
                status['overall_status'] = 'STOPPING'
                status['status_message'] = 'Daemon running but marked for shutdown'
            else:
                status['overall_status'] = 'OFFLINE'
                status['status_message'] = 'Trading bot is offline'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting trading status: {e}")
            return {
                'overall_status': 'ERROR',
                'status_message': f'Error getting status: {str(e)}',
                'daemon_running': False,
                'database_running': False
            }
    
    def restart_if_needed(self) -> Tuple[bool, str]:
        """
        Check if daemon should be running and restart if needed
        
        Returns:
            Tuple of (action_taken, message)
        """
        try:
            status = self.get_trading_status()
            
            # If database says bot should be running but daemon isn't
            if status['database_running'] and not status['daemon_running']:
                logger.info("Database indicates bot should be running - attempting restart")
                
                # Get configuration from database
                config = status.get('configuration', {})
                paper_trading = status['trading_mode'] == 'Paper Trading'
                
                # Attempt restart
                success, message = self.start_background_trading(
                    paper_trading=paper_trading,
                    risk_percentage=status['risk_percentage'],
                    max_risk_amount=status['max_risk_amount']
                )
                
                if success:
                    return True, f"Auto-restarted trading daemon: {message}"
                else:
                    return False, f"Failed to auto-restart daemon: {message}"
            
            # If daemon is running but database says it shouldn't
            elif status['daemon_running'] and not status['database_running']:
                logger.info("Daemon running but database indicates stop - shutting down")
                success, message = self.stop_background_trading()
                
                if success:
                    return True, f"Auto-stopped trading daemon: {message}"
                else:
                    return False, f"Failed to auto-stop daemon: {message}"
            
            # Everything is in sync
            else:
                return False, "No action needed - daemon and database in sync"
                
        except Exception as e:
            logger.error(f"Error in restart_if_needed: {e}")
            return False, f"Error checking restart: {str(e)}"
    
    def get_daemon_logs(self, lines: int = 50) -> str:
        """
        Get recent daemon log entries
        
        Args:
            lines: Number of recent lines to return
            
        Returns:
            Recent log entries as string
        """
        try:
            log_file = "daemon.log"
            if not os.path.exists(log_file):
                return "No daemon log file found"
            
            # Read last N lines
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
                
        except Exception as e:
            return f"Error reading daemon logs: {str(e)}"
    
    def force_cleanup(self) -> Tuple[bool, str]:
        """
        Force cleanup of daemon files and database state
        Use this if daemon gets stuck
        
        Returns:
            Tuple of (success, message)
        """
        try:
            messages = []
            
            # Stop daemon if running
            if self.daemon.is_daemon_running():
                success, msg = self.stop_background_trading()
                messages.append(f"Daemon stop: {msg}")
            
            # Clean up files
            files_to_remove = ["trading_daemon.pid", "daemon_status.json", "daemon.log"]
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    messages.append(f"Removed {file_path}")
            
            # Reset database state
            self.data_manager.save_bot_state(
                is_running=False,
                trading_mode='Paper Trading',
                risk_percentage=1.0,
                max_risk_amount=1000.0,
                session_id='cleanup',
                configuration={'force_cleanup': datetime.now().isoformat()}
            )
            messages.append("Reset database state")
            
            return True, "; ".join(messages)
            
        except Exception as e:
            logger.error(f"Error in force cleanup: {e}")
            return False, f"Cleanup error: {str(e)}"


# Singleton instance for use across the application
daemon_manager = DaemonManager()


def test_daemon_manager():
    """Test daemon manager functionality"""
    print("🔍 Testing Daemon Manager...")
    
    dm = DaemonManager()
    
    # Test status
    status = dm.get_trading_status()
    print(f"Initial status: {status['overall_status']}")
    
    # Test start
    success, message = dm.start_background_trading(paper_trading=True, risk_percentage=1.5)
    print(f"Start result: {success} - {message}")
    
    if success:
        time.sleep(3)
        
        # Test status after start
        status = dm.get_trading_status()
        print(f"Running status: {status['overall_status']} - PID: {status['daemon_pid']}")
        
        # Test stop
        success, message = dm.stop_background_trading()
        print(f"Stop result: {success} - {message}")
    
    print("Daemon Manager test complete")


if __name__ == "__main__":
    test_daemon_manager()
