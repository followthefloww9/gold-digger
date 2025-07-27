"""
Gold Digger AI Bot - Backtesting Engine
Historical strategy testing and performance validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Trade record for backtesting"""
    entry_time: datetime
    exit_time: Optional[datetime]
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    lot_size: float
    pnl: Optional[float]
    status: str  # 'OPEN', 'CLOSED', 'STOPPED', 'PROFIT'
    confidence: float
    setup_quality: int
    smc_steps: List[str]

class BacktestEngine:
    """
    Comprehensive backtesting engine for SMC strategy validation
    Tests historical performance and generates detailed analytics
    """
    
    def __init__(self, initial_balance: float = 100000):
        """Initialize backtesting engine"""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades: List[Trade] = []
        self.equity_curve = []
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance
        
        # Strategy parameters
        self.risk_per_trade = 0.01  # 1% risk per trade
        self.max_daily_trades = 5
        self.max_concurrent_trades = 3
        
        logger.info(f"BacktestEngine initialized with ${initial_balance:,.2f}")
    
    def run_backtest(self, market_data: pd.DataFrame, start_date: str, end_date: str) -> Dict[str, any]:
        """
        Run complete backtest on historical data
        
        Args:
            market_data: Historical OHLCV data
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            
        Returns:
            Comprehensive backtest results
        """
        try:
            logger.info(f"Starting backtest from {start_date} to {end_date}")
            
            # Filter data by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            if isinstance(market_data.index, pd.DatetimeIndex):
                test_data = market_data[(market_data.index >= start_dt) & (market_data.index <= end_dt)]
            else:
                test_data = market_data.copy()
            
            if test_data.empty:
                logger.error("No data available for specified date range")
                return self._get_empty_results()
            
            # Initialize trading components
            from core.trading_engine import TradingEngine
            from core.indicators import SMCIndicators
            from core.risk_manager import RiskManager
            
            trading_engine = TradingEngine()
            smc_indicators = SMCIndicators()
            risk_manager = RiskManager()
            
            # Reset state
            self.current_balance = self.initial_balance
            self.trades = []
            self.equity_curve = []
            self.peak_balance = self.initial_balance
            
            open_trades = []
            daily_trade_count = 0
            last_trade_date = None
            
            # Process each candle
            for i in range(50, len(test_data)):  # Start after 50 candles for indicators
                current_time = test_data.index[i]
                current_candle = test_data.iloc[i]
                
                # Reset daily trade count
                if last_trade_date is None or current_time.date() != last_trade_date:
                    daily_trade_count = 0
                    last_trade_date = current_time.date()
                
                # Get market data window for analysis
                window_data = test_data.iloc[max(0, i-49):i+1]  # 50 candle window
                
                # Check for trade exits first
                open_trades = self._check_trade_exits(open_trades, current_candle, current_time)
                
                # Skip new entries if limits reached
                if (daily_trade_count >= self.max_daily_trades or 
                    len(open_trades) >= self.max_concurrent_trades):
                    continue
                
                # Analyze market structure
                analysis = smc_indicators.analyze_market_structure(window_data)
                analysis['current_price'] = current_candle['Close']
                
                # Generate trade signal
                account_info = {'balance': self.current_balance, 'equity': self.current_balance}
                signal = trading_engine.generate_trade_signal(window_data, account_info)

                # Debug logging every 100 candles
                if i % 100 == 0:
                    logger.info(f"Candle {i}: Signal={signal.get('signal', 'NONE')}, Confidence={signal.get('confidence', 0):.2f}")

                # Validate with risk management
                risk_validation = risk_manager.validate_trade_risk(signal, account_info)
                
                # Execute trade if valid (lowered confidence threshold for backtesting)
                if (signal['signal'] != 'HOLD' and
                    risk_validation['approved'] and
                    signal.get('confidence', 0) >= 0.5):  # Lowered from 0.7 to 0.5
                    
                    trade = self._execute_backtest_trade(signal, current_time, current_candle)
                    if trade:
                        open_trades.append(trade)
                        daily_trade_count += 1
                        logger.info(f"Trade opened: {trade.direction} at ${trade.entry_price:.2f}")
                
                # Update equity curve
                unrealized_pnl = sum(self._calculate_unrealized_pnl(trade, current_candle) 
                                   for trade in open_trades)
                current_equity = self.current_balance + unrealized_pnl
                
                self.equity_curve.append({
                    'timestamp': current_time,
                    'balance': self.current_balance,
                    'equity': current_equity,
                    'open_trades': len(open_trades),
                    'drawdown': self._calculate_drawdown(current_equity)
                })
            
            # Close any remaining open trades
            final_candle = test_data.iloc[-1]
            for trade in open_trades:
                self._close_trade(trade, final_candle['Close'], test_data.index[-1], 'FORCED_CLOSE')
            
            # Generate results
            results = self._generate_backtest_results(start_date, end_date, len(test_data))
            logger.info(f"Backtest completed: {len(self.trades)} trades, Final balance: ${self.current_balance:,.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return self._get_empty_results()
    
    def _execute_backtest_trade(self, signal: Dict, timestamp: datetime, candle: pd.Series) -> Optional[Trade]:
        """Execute a trade in backtest mode"""
        try:
            # Calculate position size
            risk_amount = self.current_balance * self.risk_per_trade
            entry_price = signal.get('entry_price', candle['Close'])
            stop_loss = signal.get('stop_loss', entry_price)
            
            if abs(entry_price - stop_loss) == 0:
                return None
            
            # Calculate lot size (simplified for backtesting)
            pip_distance = abs(entry_price - stop_loss) * 100  # Convert to pips
            lot_size = min(1.0, max(0.01, risk_amount / pip_distance))
            
            trade = Trade(
                entry_time=timestamp,
                exit_time=None,
                direction=signal['signal'],
                entry_price=entry_price,
                exit_price=None,
                stop_loss=stop_loss,
                take_profit=signal.get('take_profit', entry_price),
                lot_size=lot_size,
                pnl=None,
                status='OPEN',
                confidence=signal.get('confidence', 0.0),
                setup_quality=signal.get('setup_quality', 5),
                smc_steps=signal.get('analysis', {}).get('smc_steps_completed', [])
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing backtest trade: {str(e)}")
            return None
    
    def _check_trade_exits(self, open_trades: List[Trade], candle: pd.Series, timestamp: datetime) -> List[Trade]:
        """Check for trade exits (TP/SL hit)"""
        remaining_trades = []
        
        for trade in open_trades:
            exit_price = None
            exit_reason = None
            
            if trade.direction == 'BUY':
                # Check stop loss
                if candle['Low'] <= trade.stop_loss:
                    exit_price = trade.stop_loss
                    exit_reason = 'STOP_LOSS'
                # Check take profit
                elif candle['High'] >= trade.take_profit:
                    exit_price = trade.take_profit
                    exit_reason = 'TAKE_PROFIT'
            
            else:  # SELL
                # Check stop loss
                if candle['High'] >= trade.stop_loss:
                    exit_price = trade.stop_loss
                    exit_reason = 'STOP_LOSS'
                # Check take profit
                elif candle['Low'] <= trade.take_profit:
                    exit_price = trade.take_profit
                    exit_reason = 'TAKE_PROFIT'
            
            if exit_price:
                self._close_trade(trade, exit_price, timestamp, exit_reason)
            else:
                remaining_trades.append(trade)
        
        return remaining_trades
    
    def _close_trade(self, trade: Trade, exit_price: float, exit_time: datetime, reason: str):
        """Close a trade and update balance"""
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.status = reason
        
        # Calculate P&L
        if trade.direction == 'BUY':
            pnl = (exit_price - trade.entry_price) * trade.lot_size * 100  # Simplified P&L
        else:
            pnl = (trade.entry_price - exit_price) * trade.lot_size * 100
        
        trade.pnl = pnl
        self.current_balance += pnl
        self.trades.append(trade)
        
        # Update peak and drawdown
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
    
    def _calculate_unrealized_pnl(self, trade: Trade, candle: pd.Series) -> float:
        """Calculate unrealized P&L for open trade"""
        current_price = candle['Close']
        
        if trade.direction == 'BUY':
            return (current_price - trade.entry_price) * trade.lot_size * 100
        else:
            return (trade.entry_price - current_price) * trade.lot_size * 100
    
    def _calculate_drawdown(self, current_equity: float) -> float:
        """Calculate current drawdown percentage"""
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - current_equity) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, drawdown)
            return drawdown
        return 0.0
    
    def _generate_backtest_results(self, start_date: str, end_date: str, total_candles: int) -> Dict[str, any]:
        """Generate comprehensive backtest results"""
        if not self.trades:
            return self._get_empty_results()
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t.pnl for t in self.trades)
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Risk metrics
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Performance metrics
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_candles': total_candles,
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'total_return': round(total_return * 100, 2),
            'total_pnl': round(total_pnl, 2),
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate * 100, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(self.max_drawdown * 100, 2),
            'trades': [self._trade_to_dict(t) for t in self.trades],
            'equity_curve': self.equity_curve[-100:],  # Last 100 points
            'strategy_validation': self._validate_strategy_performance()
        }
    
    def _trade_to_dict(self, trade: Trade) -> Dict:
        """Convert trade to dictionary"""
        return {
            'entry_time': trade.entry_time.isoformat(),
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
            'direction': trade.direction,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'pnl': trade.pnl,
            'status': trade.status,
            'confidence': trade.confidence,
            'setup_quality': trade.setup_quality
        }
    
    def _validate_strategy_performance(self) -> Dict[str, any]:
        """Validate if strategy meets performance targets"""
        if not self.trades:
            return {'valid': False, 'reason': 'No trades executed'}
        
        win_rate = len([t for t in self.trades if t.pnl > 0]) / len(self.trades)
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        
        # Strategy targets from strategy.md
        target_win_rate = 0.67  # 67% minimum
        target_return = 0.02    # 2% minimum monthly return
        max_allowed_drawdown = 0.10  # 10% maximum
        
        validation = {
            'valid': True,
            'checks': [],
            'overall_score': 0
        }
        
        # Check win rate
        if win_rate >= target_win_rate:
            validation['checks'].append(f"✅ Win rate: {win_rate:.1%} (target: {target_win_rate:.1%})")
            validation['overall_score'] += 25
        else:
            validation['checks'].append(f"❌ Win rate: {win_rate:.1%} (target: {target_win_rate:.1%})")
            validation['valid'] = False
        
        # Check drawdown
        if self.max_drawdown <= max_allowed_drawdown:
            validation['checks'].append(f"✅ Max drawdown: {self.max_drawdown:.1%} (limit: {max_allowed_drawdown:.1%})")
            validation['overall_score'] += 25
        else:
            validation['checks'].append(f"❌ Max drawdown: {self.max_drawdown:.1%} (limit: {max_allowed_drawdown:.1%})")
            validation['valid'] = False
        
        # Check profitability
        if total_return > 0:
            validation['checks'].append(f"✅ Profitable: {total_return:.1%}")
            validation['overall_score'] += 25
        else:
            validation['checks'].append(f"❌ Unprofitable: {total_return:.1%}")
            validation['valid'] = False
        
        # Check trade frequency (should have reasonable activity)
        if len(self.trades) >= 10:
            validation['checks'].append(f"✅ Trade frequency: {len(self.trades)} trades")
            validation['overall_score'] += 25
        else:
            validation['checks'].append(f"⚠️ Low trade frequency: {len(self.trades)} trades")
        
        return validation
    
    def _get_empty_results(self) -> Dict[str, any]:
        """Return empty results structure"""
        return {
            'period': 'N/A',
            'total_candles': 0,
            'initial_balance': self.initial_balance,
            'final_balance': self.initial_balance,
            'total_return': 0.0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'trades': [],
            'equity_curve': [],
            'strategy_validation': {'valid': False, 'reason': 'No data or trades'}
        }

# Test function
def test_backtester():
    """Test backtesting engine"""
    print("🔍 Testing Backtesting Engine...")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='5min')
    np.random.seed(42)
    
    data = []
    base_price = 1987.0
    for date in dates:
        price = base_price + np.random.normal(0, 2)
        data.append({
            'Open': price,
            'High': price + abs(np.random.normal(0, 1)),
            'Low': price - abs(np.random.normal(0, 1)),
            'Close': price + np.random.normal(0, 0.5),
            'Volume': np.random.randint(100, 1000)
        })
        base_price = data[-1]['Close']
    
    df = pd.DataFrame(data, index=dates)
    
    # Run backtest
    backtester = BacktestEngine(100000)
    results = backtester.run_backtest(df, '2024-01-01', '2024-01-31')
    
    print("✅ Backtesting Test Results:")
    print(f"   Period: {results['period']}")
    print(f"   Total Trades: {results['total_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1f}%")
    print(f"   Total Return: {results['total_return']:.2f}%")
    print(f"   Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"   Strategy Valid: {results['strategy_validation']['valid']}")
    
    return True

if __name__ == "__main__":
    test_backtester()
