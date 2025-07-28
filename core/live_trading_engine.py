"""
Gold Digger AI Bot - Live Trading Engine
Automated trading execution with real-time monitoring
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import json

from .mt5_connector import MT5Connector
from .gemini_client import GeminiClient
from .indicators import SMCIndicators
from .trading_engine import TradingEngine
from .risk_manager import RiskManager
from utils.data_manager import DataManager
from utils.notifications import NotificationManager
from utils.logger import get_logger

# Set up logging
logger = get_logger("live_trading")

@dataclass
class LivePosition:
    """Live position tracking"""
    ticket: int
    symbol: str
    direction: str
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    status: str = 'OPEN'

class LiveTradingEngine:
    """
    Automated live trading engine for Gold Digger AI Bot
    Executes trades based on SMC strategy and AI validation
    """
    
    def __init__(self, paper_trading: bool = True):
        """
        Initialize live trading engine
        
        Args:
            paper_trading: If True, trades are simulated (default for safety)
        """
        self.paper_trading = paper_trading
        self.is_running = False
        self.trading_thread = None
        self.gemini_available = True  # Will be set during connection test
        
        # Initialize components
        self.mt5_connector = MT5Connector()
        self.gemini_client = GeminiClient()
        self.smc_indicators = SMCIndicators()
        self.trading_engine = TradingEngine()
        self.risk_manager = RiskManager()
        self.data_manager = DataManager()
        self.notification_manager = NotificationManager()
        
        # Trading state
        self.open_positions: List[LivePosition] = []
        self.last_analysis_time = None
        self.daily_trade_count = 0
        self.last_trade_date = None
        
        # Configuration
        self.analysis_interval = 60  # Analyze every 60 seconds
        self.max_positions = 3
        self.max_daily_trades = 5
        
        logger.info(f"LiveTradingEngine initialized - Paper Trading: {paper_trading}")
    
    def start_trading(self) -> bool:
        """
        Start the live trading engine
        
        Returns:
            True if started successfully
        """
        try:
            if self.is_running:
                logger.warning("Trading engine already running")
                return False
            
            # Initialize MT5 connection
            init_result = self.mt5_connector.initialize_mt5()
            if not init_result['success']:
                logger.error(f"Failed to initialize MT5: {init_result['error']}")
                return False
            
            # Test Gemini connection (non-blocking)
            try:
                gemini_test = self.gemini_client.test_connection()
                if not gemini_test['success']:
                    logger.warning(f"Gemini AI connection issue: {gemini_test.get('error', 'Unknown error')}")
                    logger.info("Bot will continue with limited AI features")
                    self.gemini_available = False
                else:
                    logger.info("Gemini AI connected successfully")
                    self.gemini_available = True
            except Exception as e:
                logger.warning(f"Gemini AI initialization failed: {str(e)}")
                logger.info("Bot will continue with limited AI features")
                self.gemini_available = False
            
            # Reset daily counters if new day
            self._check_new_trading_day()
            
            # Start trading thread
            self.is_running = True
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()
            
            # Send startup notification
            self.notification_manager.send_system_alert(
                'SUCCESS',
                f'Gold Digger AI Bot started - Paper Trading: {self.paper_trading}',
                'INFO'
            )
            
            logger.info("Live trading engine started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {str(e)}")
            return False
    
    def stop_trading(self) -> bool:
        """
        Stop the live trading engine
        
        Returns:
            True if stopped successfully
        """
        try:
            if not self.is_running:
                logger.warning("Trading engine not running")
                return False
            
            self.is_running = False
            
            # Wait for trading thread to finish
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=10)
            
            # Close all open positions if requested
            # self._close_all_positions()  # Uncomment for emergency stop
            
            # Disconnect MT5
            self.mt5_connector.disconnect()
            
            # Send shutdown notification
            self.notification_manager.send_system_alert(
                'INFO',
                'Gold Digger AI Bot stopped',
                'INFO'
            )
            
            logger.info("Live trading engine stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {str(e)}")
            return False
    
    def _trading_loop(self):
        """Main trading loop - runs in separate thread"""
        logger.info("Trading loop started")
        
        while self.is_running:
            try:
                # Check if it's a new trading day
                self._check_new_trading_day()
                
                # Update open positions
                self._update_open_positions()
                
                # Check for new trading opportunities
                if self._should_analyze_market():
                    self._analyze_and_trade()
                
                # Sleep before next iteration
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                time.sleep(30)  # Wait longer on error
        
        logger.info("Trading loop ended")
    
    def _should_analyze_market(self) -> bool:
        """Check if we should analyze the market for new trades"""
        
        # Check daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            return False
        
        # Check position limit
        if len(self.open_positions) >= self.max_positions:
            return False
        
        # Check market hours (optional - gold trades 24/5)
        market_status = self.mt5_connector.check_market_hours()
        if not market_status.get('market_open', True):
            return False
        
        # Check time since last analysis
        if self.last_analysis_time:
            time_diff = datetime.now() - self.last_analysis_time
            if time_diff.total_seconds() < self.analysis_interval:
                return False
        
        return True
    
    def _analyze_and_trade(self):
        """Analyze market and execute trades if conditions are met"""
        try:
            logger.info("Analyzing market for trading opportunities...")
            
            # Get market data
            market_data = self.mt5_connector.get_market_data('XAUUSD', 'M5', 200)
            if market_data is None or market_data.empty:
                logger.warning("No market data available")
                return
            
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                logger.warning("No account info available")
                return
            
            # Generate technical signal first (always use technical analysis)
            signal = self.trading_engine.generate_trade_signal(market_data, account_info)

            # Enhance signal with AI validation if available
            if self.gemini_available and signal['signal'] != 'HOLD':
                try:
                    logger.info("Enhancing signal with Gemini AI validation")
                    ai_decision = self.gemini_client.get_trade_decision({
                        'current_price': signal.get('analysis', {}).get('current_price', 0),
                        'technical_signal': signal['signal'],
                        'confidence': signal['confidence'],
                        'setup_quality': signal['setup_quality'],
                        'entry_price': signal['entry_price'],
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'risk_reward_ratio': signal['risk_reward_ratio'],
                        'market_data': market_data
                    })

                    # AI can override or enhance the signal
                    if ai_decision and ai_decision.get('trade_decision') != 'HOLD':
                        # AI confirms the trade - enhance confidence
                        signal['ai_validated'] = True
                        signal['ai_confidence'] = ai_decision.get('confidence_score', 0.5)
                        signal['ai_reasoning'] = ai_decision.get('reasoning', 'AI validation')
                        signal['confidence'] = min(1.0, signal['confidence'] + 0.2)  # Boost confidence
                        logger.info(f"✅ AI validated {signal['signal']} signal (AI confidence: {signal['ai_confidence']:.2f})")
                    else:
                        # AI suggests HOLD - reduce confidence or override
                        signal['ai_validated'] = False
                        signal['ai_confidence'] = ai_decision.get('confidence_score', 0.0)
                        signal['ai_reasoning'] = ai_decision.get('reasoning', 'AI suggests caution')
                        signal['confidence'] = max(0.0, signal['confidence'] - 0.3)  # Reduce confidence

                        # If AI strongly disagrees, override to HOLD
                        if signal['confidence'] < 0.3:
                            signal['signal'] = 'HOLD'
                            signal['reasons'].append('AI validation failed')

                        logger.info(f"⚠️ AI suggests caution for {signal['signal']} signal")

                except Exception as e:
                    logger.warning(f"AI validation failed: {e}")
                    signal['ai_validated'] = False
                    signal['ai_reasoning'] = f"AI validation error: {str(e)}"
            else:
                # Technical analysis only
                if not self.gemini_available:
                    logger.info("Using technical analysis only (Gemini AI unavailable)")
                signal['ai_validated'] = False
                signal['ai_reasoning'] = 'AI not available' if not self.gemini_available else 'Technical signal only'
            
            # Log analysis
            self.data_manager.save_market_analysis({
                'timeframe': 'M5',
                'current_price': signal.get('analysis', {}).get('current_price', 0),
                'trend': signal.get('analysis', {}).get('trend', 'NEUTRAL'),
                'session': 'UNKNOWN',
                'setup_quality': signal.get('setup_quality', 0),
                'ai_confidence': signal.get('confidence', 0)
            })
            
            # Check if we have a valid signal
            if signal['signal'] != 'HOLD' and signal.get('confidence', 0) >= 0.75:
                
                # Validate with risk management
                risk_validation = self.risk_manager.validate_trade_risk(signal, account_info)
                
                if risk_validation['approved']:
                    # Execute the trade
                    self._execute_trade(signal, risk_validation)
                else:
                    logger.info(f"Trade rejected by risk management: {risk_validation['reasons']}")
            
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
    
    def _execute_trade(self, signal: Dict, risk_validation: Dict):
        """Execute a validated trade"""
        try:
            symbol = 'XAUUSD'
            direction = signal['signal']
            volume = risk_validation['adjusted_lot_size']
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            take_profit = signal.get('take_profit', 0)
            
            logger.info(f"Executing trade: {direction} {volume} lots {symbol}")
            
            # Execute trade via MT5
            if self.paper_trading:
                # Paper trading execution
                result = {
                    'success': True,
                    'ticket': len(self.open_positions) + 1000,
                    'volume': volume,
                    'price': entry_price,
                    'mode': 'PAPER_TRADING'
                }
            else:
                # Real trading execution
                result = self.mt5_connector.open_trade(
                    symbol, direction, volume, stop_loss, take_profit
                )
            
            if result['success']:
                # Create position record
                position = LivePosition(
                    ticket=result['ticket'],
                    symbol=symbol,
                    direction=direction,
                    volume=volume,
                    entry_price=result['price'],
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_time=datetime.now()
                )
                
                self.open_positions.append(position)
                self.daily_trade_count += 1
                
                # Save trade to database
                trade_data = {
                    'entry_time': position.entry_time,
                    'direction': direction,
                    'entry_price': result['price'],
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'lot_size': volume,
                    'status': 'OPEN',
                    'confidence': signal.get('confidence', 0),
                    'setup_quality': signal.get('setup_quality', 0),
                    'smc_steps': signal.get('analysis', {}).get('smc_steps_completed', []),
                    'reasoning': signal.get('reasons', [''])[0] if signal.get('reasons') else '',
                    'session': 'UNKNOWN',
                    'timeframe': 'M5'
                }
                
                self.data_manager.save_trade(trade_data)
                
                # Send notification
                market_data = {
                    'current_price': result['price'],
                    'session': 'UNKNOWN'
                }
                
                self.notification_manager.send_trade_alert(signal, market_data)
                
                logger.info(f"Trade executed successfully: Ticket {result['ticket']}")
                
            else:
                logger.error(f"Trade execution failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
    
    def _update_open_positions(self):
        """Update open positions with current prices and check for exits"""
        if not self.open_positions:
            return
        
        try:
            current_price_data = self.mt5_connector.get_current_price('XAUUSD')
            if not current_price_data:
                return
            
            current_price = current_price_data['last']
            
            positions_to_remove = []
            
            for i, position in enumerate(self.open_positions):
                # Update current price and P&L
                position.current_price = current_price
                
                if position.direction == 'BUY':
                    position.unrealized_pnl = (current_price - position.entry_price) * position.volume * 100
                    
                    # Check for exit conditions
                    if current_price <= position.stop_loss:
                        self._close_position(position, current_price, 'STOP_LOSS')
                        positions_to_remove.append(i)
                    elif current_price >= position.take_profit:
                        self._close_position(position, current_price, 'TAKE_PROFIT')
                        positions_to_remove.append(i)
                        
                else:  # SELL
                    position.unrealized_pnl = (position.entry_price - current_price) * position.volume * 100
                    
                    # Check for exit conditions
                    if current_price >= position.stop_loss:
                        self._close_position(position, current_price, 'STOP_LOSS')
                        positions_to_remove.append(i)
                    elif current_price <= position.take_profit:
                        self._close_position(position, current_price, 'TAKE_PROFIT')
                        positions_to_remove.append(i)
            
            # Remove closed positions
            for i in reversed(positions_to_remove):
                self.open_positions.pop(i)
                
        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
    
    def _close_position(self, position: LivePosition, exit_price: float, reason: str):
        """Close a position and record the result"""
        try:
            logger.info(f"Closing position {position.ticket}: {reason} at {exit_price}")
            
            # Close via MT5 (or simulate for paper trading)
            if not self.paper_trading:
                close_result = self.mt5_connector.close_trade(position.ticket)
                if not close_result['success']:
                    logger.error(f"Failed to close position: {close_result.get('error')}")
                    return
            
            # Calculate final P&L
            if position.direction == 'BUY':
                pnl = (exit_price - position.entry_price) * position.volume * 100
            else:
                pnl = (position.entry_price - exit_price) * position.volume * 100
            
            # Update trade record in database
            trade_data = {
                'entry_time': position.entry_time,
                'exit_time': datetime.now(),
                'direction': position.direction,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'lot_size': position.volume,
                'pnl': pnl,
                'status': reason,
                'confidence': 0,  # Will be updated from original trade
                'setup_quality': 0,
                'smc_steps': [],
                'reasoning': f'Closed: {reason}',
                'session': 'UNKNOWN',
                'timeframe': 'M5'
            }
            
            self.data_manager.save_trade(trade_data)
            
            # Update risk manager
            self.risk_manager.update_daily_pnl(pnl)
            
            logger.info(f"Position closed: P&L ${pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
    
    def _check_new_trading_day(self):
        """Check if it's a new trading day and reset counters"""
        current_date = datetime.now().date()
        
        if self.last_trade_date != current_date:
            self.daily_trade_count = 0
            self.risk_manager.reset_daily_counters()
            self.last_trade_date = current_date
            logger.info(f"New trading day: {current_date}")
    
    def get_status(self) -> Dict[str, any]:
        """Get current trading engine status"""
        return {
            'is_running': self.is_running,
            'paper_trading': self.paper_trading,
            'open_positions': len(self.open_positions),
            'daily_trades': self.daily_trade_count,
            'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'positions': [
                {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'direction': pos.direction,
                    'volume': pos.volume,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'entry_time': pos.entry_time.isoformat()
                }
                for pos in self.open_positions
            ]
        }

# Test function
def test_live_trading_engine():
    """Test live trading engine in paper mode"""
    print("🔍 Testing Live Trading Engine...")
    
    # Create engine in paper trading mode
    engine = LiveTradingEngine(paper_trading=True)
    
    # Test initialization
    status = engine.get_status()
    
    print("✅ Live Trading Engine Test Results:")
    print(f"   Paper Trading: {status['paper_trading']}")
    print(f"   Running: {status['is_running']}")
    print(f"   Open Positions: {status['open_positions']}")
    print(f"   Daily Trades: {status['daily_trades']}")
    
    return True

if __name__ == "__main__":
    test_live_trading_engine()
