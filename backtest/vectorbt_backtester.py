#!/usr/bin/env python3
"""
Gold Digger AI Bot - VectorBT Backtesting Engine
Fast, accurate backtesting using VectorBT library for macOS compatibility
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    print("VectorBT not available - using fallback backtesting")

class VectorBTBacktester:
    """
    Professional backtesting engine using VectorBT
    Works perfectly on macOS without MT5 dependency
    """
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.results = {}
        
    def get_gold_data(self, start_date, end_date, interval='5m'):
        """Get real gold market data from Yahoo Finance"""
        try:
            # Calculate period for optimal data retrieval
            days_diff = (end_date - start_date).days
            
            if days_diff <= 7:
                period = "7d"
                interval = "5m"
            elif days_diff <= 30:
                period = "1mo" 
                interval = "5m"
            elif days_diff <= 90:
                period = "3mo"
                interval = "15m"
            else:
                period = "1y"
                interval = "1h"
            
            # Fetch real gold futures data
            ticker = yf.Ticker('GC=F')
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                # Fallback to longer period
                data = ticker.history(period="1y", interval="1d")
            
            # Filter by date range (handle timezone issues)
            start_dt = pd.to_datetime(start_date).tz_localize(None)
            end_dt = (pd.to_datetime(end_date) + pd.Timedelta(days=1)).tz_localize(None)

            # Remove timezone from data index if present
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)

            mask = (data.index >= start_dt) & (data.index <= end_dt)
            filtered_data = data.loc[mask]
            
            if filtered_data.empty:
                # Use most recent data if no data in range
                filtered_data = data.tail(500)
            
            return filtered_data
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def smc_strategy_signals(self, data):
        """
        Generate Smart Money Concepts trading signals
        Simplified but effective strategy for backtesting
        """
        if len(data) < 50:
            return pd.Series(False, index=data.index), pd.Series(False, index=data.index)
        
        # Calculate indicators
        close = data['Close']
        high = data['High']
        low = data['Low']
        
        # Moving averages for trend
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        
        # RSI for momentum
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Support and Resistance levels
        rolling_high = high.rolling(20).max()
        rolling_low = low.rolling(20).min()
        
        # More aggressive buy signals for better backtesting
        buy_signals = (
            (ema_12 > ema_26) &  # Momentum up
            (rsi < 75) &         # Not extremely overbought
            (close > sma_20) &   # Above short-term trend
            (close > rolling_low * 1.002)  # Above recent support
        )

        # More aggressive sell signals
        sell_signals = (
            (ema_12 < ema_26) &  # Momentum down
            (rsi > 25) &         # Not extremely oversold
            (close < sma_20) &   # Below short-term trend
            (close < rolling_high * 0.998)  # Below recent resistance
        )
        
        return buy_signals.fillna(False), sell_signals.fillna(False)
    
    def run_vectorbt_backtest(self, start_date, end_date):
        """Run backtest using VectorBT for maximum performance"""
        try:
            # Get market data
            data = self.get_gold_data(start_date, end_date)
            
            if data.empty:
                return self._empty_results()
            
            if not VECTORBT_AVAILABLE:
                return self._fallback_backtest(data)
            
            # Generate signals
            buy_signals, sell_signals = self.smc_strategy_signals(data)
            
            # Create entries and exits
            entries = buy_signals
            exits = sell_signals
            
            # Run VectorBT simulation
            portfolio = vbt.Portfolio.from_signals(
                data['Close'],
                entries=entries,
                exits=exits,
                init_cash=self.initial_capital,
                fees=0.001,  # 0.1% fee per trade
                freq='5T'    # 5-minute frequency
            )
            
            # Extract results
            total_return = portfolio.total_return() * 100
            win_rate = portfolio.trades.win_rate * 100 if portfolio.trades.count > 0 else 0
            max_drawdown = abs(portfolio.max_drawdown() * 100)
            total_trades = portfolio.trades.count
            
            # Calculate additional metrics
            sharpe_ratio = portfolio.sharpe_ratio()
            profit_factor = portfolio.trades.profit_factor if portfolio.trades.count > 0 else 0
            
            return {
                'total_return': total_return,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'sharpe_ratio': sharpe_ratio,
                'profit_factor': profit_factor,
                'equity_curve': portfolio.value(),
                'trades': portfolio.trades.records_readable if portfolio.trades.count > 0 else pd.DataFrame(),
                'success': True,
                'data_points': len(data),
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            print(f"VectorBT backtest error: {e}")
            return self._fallback_backtest(data)
    
    def _fallback_backtest(self, data):
        """Fallback backtesting when VectorBT is not available"""
        try:
            if data.empty:
                return self._empty_results()
            
            # Simple strategy implementation
            buy_signals, sell_signals = self.smc_strategy_signals(data)
            
            # Manual backtesting
            capital = self.initial_capital
            position = 0
            trades = []
            equity_curve = [capital]
            
            for i in range(len(data)):
                current_price = data['Close'].iloc[i]
                
                # Buy signal
                if buy_signals.iloc[i] and position == 0:
                    position = capital / current_price  # Buy with all capital
                    capital = 0
                    entry_price = current_price
                    entry_time = data.index[i]
                
                # Sell signal
                elif sell_signals.iloc[i] and position > 0:
                    capital = position * current_price  # Sell all position
                    pnl = capital - self.initial_capital
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': data.index[i],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'return_pct': (current_price - entry_price) / entry_price * 100
                    })
                    
                    position = 0
                
                # Update equity curve
                current_equity = capital + (position * current_price if position > 0 else 0)
                equity_curve.append(current_equity)
            
            # Calculate metrics
            if trades:
                total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital * 100
                winning_trades = [t for t in trades if t['pnl'] > 0]
                win_rate = len(winning_trades) / len(trades) * 100
                
                # Calculate max drawdown
                peak = self.initial_capital
                max_dd = 0
                for equity in equity_curve:
                    if equity > peak:
                        peak = equity
                    drawdown = (peak - equity) / peak * 100
                    max_dd = max(max_dd, drawdown)
                
                max_drawdown = max_dd
            else:
                total_return = 0
                win_rate = 0
                max_drawdown = 0
            
            return {
                'total_return': total_return,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'total_trades': len(trades),
                'sharpe_ratio': 0,
                'profit_factor': 0,
                'equity_curve': pd.Series(equity_curve, index=data.index[:len(equity_curve)]),
                'trades': pd.DataFrame(trades),
                'success': True,
                'data_points': len(data),
                'period': f"{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            print(f"Fallback backtest error: {e}")
            return self._empty_results()
    
    def _empty_results(self):
        """Return empty results when backtesting fails"""
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0,
            'sharpe_ratio': 0.0,
            'profit_factor': 0.0,
            'equity_curve': pd.Series([]),
            'trades': pd.DataFrame(),
            'success': False,
            'data_points': 0,
            'period': 'No data available'
        }

def run_quick_backtest(start_date, end_date, initial_capital=100000):
    """Quick backtest function for Streamlit integration"""
    backtester = VectorBTBacktester(initial_capital)
    return backtester.run_vectorbt_backtest(start_date, end_date)
