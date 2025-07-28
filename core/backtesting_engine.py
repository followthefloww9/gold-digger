"""
Gold Digger AI Bot - Backtesting Engine
Professional backtesting system for strategy validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from .trading_engine import TradingEngine
from .indicators import SMCIndicators

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """
    Professional backtesting engine for Gold Digger AI Bot
    Tests trading strategies against historical data
    """
    
    def __init__(self):
        """Initialize backtesting engine"""
        self.trading_engine = TradingEngine(use_mql5_bridge=False)  # No MQL5 for backtesting
        self.indicators = SMCIndicators()
        
        # Backtesting parameters
        self.commission = 0.0003  # 0.03% commission per trade
        self.spread = 0.5  # $0.50 spread for gold
        self.slippage = 0.2  # $0.20 slippage
        
        logger.info("📊 Backtesting Engine initialized")
    
    def run_backtest(self, data: pd.DataFrame, initial_balance: float = 10000,
                    start_date: Optional[datetime] = None, 
                    end_date: Optional[datetime] = None,
                    lot_size: float = 0.01) -> Dict:
        """
        Run comprehensive backtest on historical data
        
        Args:
            data: OHLC data with Time index
            initial_balance: Starting balance
            start_date: Backtest start date
            end_date: Backtest end date
            lot_size: Position size per trade
            
        Returns:
            dict: Comprehensive backtest results
        """
        try:
            logger.info(f"🔄 Starting backtest: {len(data)} candles, ${initial_balance:,.2f} initial balance")
            
            # Filter data by date range
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            if len(data) < 50:
                return {'error': 'Insufficient data for backtesting (minimum 50 candles required)'}
            
            # Initialize backtest state
            balance = initial_balance
            equity = initial_balance
            positions = []
            trades = []
            equity_curve = []
            
            # Track performance metrics
            max_balance = initial_balance
            max_drawdown = 0.0
            consecutive_losses = 0
            max_consecutive_losses = 0
            
            logger.info(f"📈 Processing {len(data)} candles from {data.index[0]} to {data.index[-1]}")
            
            # Process each candle
            for i in range(50, len(data)):  # Start after 50 candles for indicators
                current_time = data.index[i]
                current_data = data.iloc[:i+1]  # Data up to current point
                current_price = data.iloc[i]['Close']
                
                # Update equity curve
                current_equity = balance
                for pos in positions:
                    if pos['type'] == 'BUY':
                        current_equity += (current_price - pos['entry_price']) * pos['size'] * 100
                    else:  # SELL
                        current_equity += (pos['entry_price'] - current_price) * pos['size'] * 100
                
                equity = current_equity
                equity_curve.append({
                    'time': current_time,
                    'balance': balance,
                    'equity': equity
                })
                
                # Track drawdown
                if equity > max_balance:
                    max_balance = equity
                
                current_drawdown = (max_balance - equity) / max_balance * 100
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown
                
                # Generate trading signal using AI
                try:
                    # Create account info for signal generation
                    account_info = {
                        'balance': balance,
                        'equity': equity,
                        'currency': 'USD'
                    }
                    
                    signal = self.trading_engine.generate_trade_signal(current_data, account_info)
                    
                    # Process signal
                    if signal['signal'] in ['BUY', 'SELL'] and signal['confidence'] > 0.6:
                        # Check if we can open new position
                        if len(positions) == 0:  # Only one position at a time
                            # Calculate position size based on risk
                            risk_amount = balance * 0.02  # 2% risk
                            stop_loss_distance = abs(current_price - signal.get('stop_loss', current_price * 0.99))
                            if stop_loss_distance > 0:
                                position_size = min(lot_size, risk_amount / (stop_loss_distance * 100))
                            else:
                                position_size = lot_size
                            
                            # Apply costs
                            entry_cost = position_size * 100 * self.commission + self.spread + self.slippage
                            
                            if balance > entry_cost:
                                # Open position
                                position = {
                                    'type': signal['signal'],
                                    'entry_price': current_price + (self.spread if signal['signal'] == 'BUY' else -self.spread),
                                    'entry_time': current_time,
                                    'size': position_size,
                                    'stop_loss': signal.get('stop_loss', current_price * 0.99 if signal['signal'] == 'BUY' else current_price * 1.01),
                                    'take_profit': signal.get('take_profit', current_price * 1.02 if signal['signal'] == 'BUY' else current_price * 0.98),
                                    'confidence': signal['confidence']
                                }
                                
                                positions.append(position)
                                balance -= entry_cost
                                
                                logger.debug(f"📊 {signal['signal']} position opened at ${current_price:.2f}")
                    
                    # Check existing positions for exit conditions
                    positions_to_close = []
                    for j, pos in enumerate(positions):
                        should_close = False
                        exit_reason = ""
                        exit_price = current_price
                        
                        # Check stop loss
                        if pos['type'] == 'BUY' and current_price <= pos['stop_loss']:
                            should_close = True
                            exit_reason = "Stop Loss"
                            exit_price = pos['stop_loss']
                        elif pos['type'] == 'SELL' and current_price >= pos['stop_loss']:
                            should_close = True
                            exit_reason = "Stop Loss"
                            exit_price = pos['stop_loss']
                        
                        # Check take profit
                        elif pos['type'] == 'BUY' and current_price >= pos['take_profit']:
                            should_close = True
                            exit_reason = "Take Profit"
                            exit_price = pos['take_profit']
                        elif pos['type'] == 'SELL' and current_price <= pos['take_profit']:
                            should_close = True
                            exit_reason = "Take Profit"
                            exit_price = pos['take_profit']
                        
                        # Check for opposite signal
                        elif signal['signal'] == 'CLOSE' or (signal['signal'] != pos['type'] and signal['confidence'] > 0.7):
                            should_close = True
                            exit_reason = "Signal Change"
                        
                        if should_close:
                            # Close position
                            if pos['type'] == 'BUY':
                                profit = (exit_price - pos['entry_price']) * pos['size'] * 100
                            else:  # SELL
                                profit = (pos['entry_price'] - exit_price) * pos['size'] * 100
                            
                            # Apply exit costs
                            exit_cost = pos['size'] * 100 * self.commission + self.spread + self.slippage
                            net_profit = profit - exit_cost
                            
                            balance += net_profit
                            
                            # Record trade
                            trade = {
                                'entry_time': pos['entry_time'],
                                'exit_time': current_time,
                                'type': pos['type'],
                                'entry_price': pos['entry_price'],
                                'exit_price': exit_price,
                                'size': pos['size'],
                                'profit': net_profit,
                                'exit_reason': exit_reason,
                                'confidence': pos['confidence'],
                                'duration': (current_time - pos['entry_time']).total_seconds() / 3600  # hours
                            }
                            
                            trades.append(trade)
                            positions_to_close.append(j)
                            
                            # Track consecutive losses
                            if net_profit < 0:
                                consecutive_losses += 1
                                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                            else:
                                consecutive_losses = 0
                            
                            logger.debug(f"📊 Position closed: {exit_reason}, P&L: ${net_profit:.2f}")
                    
                    # Remove closed positions
                    for j in reversed(positions_to_close):
                        positions.pop(j)
                
                except Exception as e:
                    logger.debug(f"Signal generation error at {current_time}: {e}")
                    continue
            
            # Close any remaining positions at the end
            final_price = data.iloc[-1]['Close']
            for pos in positions:
                if pos['type'] == 'BUY':
                    profit = (final_price - pos['entry_price']) * pos['size'] * 100
                else:
                    profit = (pos['entry_price'] - final_price) * pos['size'] * 100
                
                exit_cost = pos['size'] * 100 * self.commission + self.spread
                net_profit = profit - exit_cost
                balance += net_profit
                
                trades.append({
                    'entry_time': pos['entry_time'],
                    'exit_time': data.index[-1],
                    'type': pos['type'],
                    'entry_price': pos['entry_price'],
                    'exit_price': final_price,
                    'size': pos['size'],
                    'profit': net_profit,
                    'exit_reason': 'End of Data',
                    'confidence': pos['confidence'],
                    'duration': (data.index[-1] - pos['entry_time']).total_seconds() / 3600
                })
            
            # Calculate performance metrics
            results = self._calculate_performance_metrics(
                initial_balance, balance, trades, equity_curve, data
            )
            
            logger.info(f"✅ Backtest completed: {len(trades)} trades, ${balance:,.2f} final balance")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Backtest error: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_metrics(self, initial_balance: float, final_balance: float,
                                     trades: List[Dict], equity_curve: List[Dict],
                                     data: pd.DataFrame) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        if not trades:
            return {
                'initial_balance': initial_balance,
                'final_balance': final_balance,
                'total_return': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0,
                'avg_trade': 0.0,
                'period': f"{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}",
                'data_points': len(data),
                'trades': [],
                'equity_curve': equity_curve
            }
        
        # Basic metrics
        total_return = (final_balance - initial_balance) / initial_balance * 100
        total_trades = len(trades)
        
        # Trade analysis
        profits = [t['profit'] for t in trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        avg_trade = sum(profits) / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Sharpe ratio (simplified)
        if len(profits) > 1:
            returns_std = np.std(profits)
            sharpe_ratio = (avg_trade / returns_std) if returns_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        max_drawdown = 0
        peak = initial_balance
        for point in equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            drawdown = (peak - point['equity']) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'avg_trade': avg_trade,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'period': f"{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}",
            'data_points': len(data),
            'trades': trades,
            'equity_curve': equity_curve,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades)
        }
