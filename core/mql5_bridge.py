"""
MQL5 Bridge - Communication layer between Python Gold Digger bot and MT5 Expert Advisor
Cross-platform compatible (macOS, Windows, Linux)
"""

import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import platform

logger = logging.getLogger(__name__)

class MQL5Bridge:
    """Bridge for communicating with MQL5 Expert Advisor"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize MQL5 Bridge
        
        Args:
            data_path: Custom data path. If None, auto-detects platform-appropriate path
        """
        self.data_path = self._setup_data_path(data_path)
        self.signal_file = self.data_path / "gold_digger_signals.json"
        self.results_file = self.data_path / "gold_digger_results.json"
        self.archive_path = self.data_path / "archive"
        
        # Ensure directories exist
        self._ensure_directories()
        
        logger.info(f"🔗 MQL5 Bridge initialized")
        logger.info(f"📁 Data path: {self.data_path}")
        logger.info(f"📊 Signal file: {self.signal_file}")
        logger.info(f"📈 Results file: {self.results_file}")
    
    def _setup_data_path(self, custom_path: Optional[str] = None) -> Path:
        """Setup cross-platform data path"""
        if custom_path:
            return Path(custom_path)
        
        system = platform.system().lower()
        
        if system == "windows":
            # Windows paths
            paths = [
                Path("C:/Users/Public/Documents/GoldDigger"),
                Path("C:/temp/GoldDigger"),
                Path.home() / "Documents" / "GoldDigger"
            ]
        elif system == "darwin":  # macOS
            # macOS paths
            paths = [
                Path("/Users/Shared/GoldDigger"),
                Path("/tmp/GoldDigger"),
                Path.home() / "Documents" / "GoldDigger"
            ]
        else:  # Linux
            # Linux paths
            paths = [
                Path("/tmp/GoldDigger"),
                Path.home() / "Documents" / "GoldDigger"
            ]
        
        # Try each path
        for path in paths:
            try:
                path.mkdir(parents=True, exist_ok=True)
                # Test write access
                test_file = path / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                logger.info(f"✅ Using data path: {path}")
                return path
            except Exception as e:
                logger.debug(f"❌ Cannot use path {path}: {e}")
                continue
        
        # Fallback to current directory
        fallback = Path.cwd() / "mql5_data"
        fallback.mkdir(exist_ok=True)
        logger.warning(f"⚠️ Using fallback path: {fallback}")
        return fallback
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)
    
    def send_signal(self, action: str, price: float = 0, stop_loss: float = 0, 
                   take_profit: float = 0, confidence: float = 0.8, 
                   analysis: str = "") -> bool:
        """
        Send trading signal to MQL5 EA
        
        Args:
            action: Trading action ("BUY", "SELL", "CLOSE", "HOLD")
            price: Entry price (0 = market price)
            stop_loss: Stop loss level (0 = auto-calculate)
            take_profit: Take profit level (0 = auto-calculate)
            confidence: AI confidence level (0.0 - 1.0)
            analysis: AI analysis text
            
        Returns:
            bool: True if signal sent successfully
        """
        try:
            signal_data = {
                "action": action.upper(),
                "price": price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "source": "Gold Digger AI Bot",
                "version": "1.0"
            }
            
            # Write signal to file
            with open(self.signal_file, 'w') as f:
                json.dump(signal_data, f, indent=2)
            
            logger.info(f"📤 Signal sent: {action} | Confidence: {confidence:.2f} | Price: {price}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send signal: {e}")
            return False
    
    def get_results(self) -> Optional[Dict[str, Any]]:
        """
        Get latest results from MQL5 EA
        
        Returns:
            dict: Results data or None if no results available
        """
        try:
            if not self.results_file.exists():
                return None
            
            with open(self.results_file, 'r') as f:
                results = json.load(f)
            
            return results
            
        except Exception as e:
            logger.debug(f"No results available: {e}")
            return None
    
    def wait_for_execution(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Wait for signal execution and return results
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            dict: Execution results or None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            results = self.get_results()
            
            if results and results.get('status') in ['BUY_SUCCESS', 'SELL_SUCCESS', 'CLOSE_SUCCESS', 
                                                    'PAPER_BUY', 'PAPER_SELL', 'PAPER_CLOSE',
                                                    'BUY_FAILED', 'SELL_FAILED', 'ERROR']:
                return results
            
            time.sleep(1)
        
        logger.warning(f"⏰ Execution timeout after {timeout} seconds")
        return None
    
    def get_account_status(self) -> Dict[str, Any]:
        """
        Get current account status from EA
        
        Returns:
            dict: Account status information
        """
        results = self.get_results()
        
        if results:
            return {
                'balance': results.get('balance', 0),
                'equity': results.get('equity', 0),
                'open_positions': results.get('open_positions', 0),
                'total_profit': results.get('total_profit', 0),
                'current_price': results.get('current_price', 0),
                'trading_mode': results.get('trading_mode', 'UNKNOWN'),
                'last_update': results.get('timestamp', ''),
                'status': results.get('status', 'UNKNOWN')
            }
        
        return {
            'balance': 0,
            'equity': 0,
            'open_positions': 0,
            'total_profit': 0,
            'current_price': 0,
            'trading_mode': 'UNKNOWN',
            'last_update': '',
            'status': 'NO_CONNECTION'
        }
    
    def is_ea_running(self) -> bool:
        """
        Check if EA is running and responding
        
        Returns:
            bool: True if EA is active
        """
        results = self.get_results()
        
        if not results:
            return False
        
        # Check if results are recent (within last 30 seconds)
        try:
            last_update = datetime.fromisoformat(results.get('timestamp', ''))
            time_diff = datetime.now() - last_update
            return time_diff.total_seconds() < 30
        except:
            return False
    
    def send_buy_signal(self, price: float = 0, stop_loss: float = 0, 
                       take_profit: float = 0, confidence: float = 0.8,
                       analysis: str = "AI Buy Signal") -> bool:
        """Send BUY signal to EA"""
        return self.send_signal("BUY", price, stop_loss, take_profit, confidence, analysis)
    
    def send_sell_signal(self, price: float = 0, stop_loss: float = 0, 
                        take_profit: float = 0, confidence: float = 0.8,
                        analysis: str = "AI Sell Signal") -> bool:
        """Send SELL signal to EA"""
        return self.send_signal("SELL", price, stop_loss, take_profit, confidence, analysis)
    
    def send_close_signal(self, analysis: str = "AI Close Signal") -> bool:
        """Send CLOSE signal to EA"""
        return self.send_signal("CLOSE", analysis=analysis)
    
    def send_hold_signal(self, analysis: str = "AI Hold Signal") -> bool:
        """Send HOLD signal to EA"""
        return self.send_signal("HOLD", analysis=analysis)
    
    def get_signal_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of processed signals
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            list: List of historical signals
        """
        history = []
        
        try:
            # Look for archived signals
            for archive_file in self.archive_path.glob("*_processed.json"):
                try:
                    with open(archive_file, 'r') as f:
                        signal_data = json.load(f)
                    history.append(signal_data)
                except:
                    continue
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to get signal history: {e}")
            return []
    
    def cleanup_old_files(self, days: int = 7):
        """
        Clean up old signal and result files
        
        Args:
            days: Remove files older than this many days
        """
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            for file_path in self.archive_path.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.debug(f"🗑️ Cleaned up old file: {file_path}")
                    
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to MQL5 EA
        
        Returns:
            dict: Connection test results
        """
        logger.info("🔍 Testing MQL5 EA connection...")
        
        # Send test signal
        test_sent = self.send_signal("HOLD", confidence=0.1, analysis="Connection test")
        
        if not test_sent:
            return {
                'success': False,
                'message': 'Failed to send test signal',
                'ea_running': False
            }
        
        # Wait for response
        time.sleep(2)
        
        # Check if EA responded
        ea_running = self.is_ea_running()
        account_status = self.get_account_status()
        
        return {
            'success': ea_running,
            'message': 'EA connection successful' if ea_running else 'EA not responding',
            'ea_running': ea_running,
            'account_status': account_status,
            'data_path': str(self.data_path),
            'files_exist': {
                'signal_file': self.signal_file.exists(),
                'results_file': self.results_file.exists()
            }
        }
