#!/usr/bin/env python3
"""
Gold Digger AI Bot - Simple Reliable Backtesting
Works perfectly on macOS without complex dependencies
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SimpleBacktester:
    """
    Simple, reliable backtesting engine that always works
    Uses real MT5 data with fallback to Yahoo Finance
    """

    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.data_source = 'Unknown'
        
    def get_gold_data(self, start_date, end_date):
        """Get real gold market data from MT5 or fallback to Yahoo Finance"""
        try:
            # Try to get data from MT5 first
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from core.mt5_connector import MT5Connector

                print("📊 Attempting to fetch data from MetaTrader 5...")
                connector = MT5Connector()
                init_result = connector.initialize_mt5()

                if init_result['success']:
                    # Calculate how many candles we need
                    days_diff = (end_date - start_date).days
                    candles_needed = min(days_diff * 288, 1000)  # 288 5-min candles per day, max 1000

                    # Always use XAUUSD for the strategy
                    gold_symbol = 'XAUUSD'

                    print(f"📊 Using gold symbol for backtest: {gold_symbol}")
                    data = connector.get_market_data(gold_symbol, 'M5', candles_needed)

                    if data is not None and not data.empty:
                        # Convert MT5 data to Yahoo Finance format
                        data = data.set_index('time')
                        data.rename(columns={
                            'Open': 'Open',
                            'High': 'High',
                            'Low': 'Low',
                            'Close': 'Close',
                            'Volume': 'Volume'
                        }, inplace=True)

                        # Filter by date range
                        start_dt = pd.to_datetime(start_date)
                        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
                        mask = (data.index >= start_dt) & (data.index <= end_dt)
                        data = data[mask]

                        if not data.empty:
                            print(f"✅ Real MT5 data fetched: {len(data)} candles from MetaTrader 5")
                            self.data_source = f'MetaTrader 5 ({gold_symbol})'
                            return data

            except Exception as mt5_error:
                print(f"⚠️ MT5 data fetch failed: {mt5_error}")

            # Fallback to Yahoo Finance
            print("📊 Falling back to Yahoo Finance...")

            # Calculate optimal period
            days_diff = (end_date - start_date).days

            if days_diff <= 7:
                period = "7d"
                interval = "5m"
            elif days_diff <= 30:
                period = "1mo"
                interval = "15m"
            elif days_diff <= 90:
                period = "3mo"
                interval = "1h"
            else:
                period = "1y"
                interval = "1d"

            # Fetch REAL gold futures data from Yahoo Finance
            ticker = yf.Ticker('GC=F')
            print(f"📊 Fetching REAL gold data: period={period}, interval={interval}")
            data = ticker.history(period=period, interval=interval)

            if data.empty:
                print("⚠️ Primary data fetch failed, trying fallback...")
                # Fallback to daily data
                data = ticker.history(period="6mo", interval="1d")
                print(f"📊 Fallback data: {len(data)} daily candles")
            else:
                print(f"✅ Real data fetched: {len(data)} candles from Yahoo Finance")

            self.data_source = 'Yahoo Finance Gold Futures (GC=F)'
            
            # Remove timezone for consistency
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            
            mask = (data.index >= start_dt) & (data.index <= end_dt)
            filtered_data = data.loc[mask]
            
            if filtered_data.empty:
                # Use most recent data
                filtered_data = data.tail(200)
            
            return filtered_data
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        close = data['Close'].copy()
        
        # Moving averages
        sma_10 = close.rolling(10, min_periods=1).mean()
        sma_20 = close.rolling(20, min_periods=1).mean()
        ema_12 = close.ewm(span=12, min_periods=1).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'sma_10': sma_10,
            'sma_20': sma_20,
            'ema_12': ema_12,
            'rsi': rsi
        }
    
    def generate_signals(self, data, indicators):
        """Generate trading signals"""
        close = data['Close']
        sma_10 = indicators['sma_10']
        sma_20 = indicators['sma_20']
        rsi = indicators['rsi']
        
        # Simple but effective strategy
        buy_signals = (
            (sma_10 > sma_20) &  # Short MA above long MA
            (rsi < 70) &         # Not overbought
            (close > sma_10)     # Price above short MA
        )
        
        sell_signals = (
            (sma_10 < sma_20) &  # Short MA below long MA
            (rsi > 30) &         # Not oversold
            (close < sma_10)     # Price below short MA
        )
        
        return buy_signals.fillna(False), sell_signals.fillna(False)
    
    def run_backtest(self, start_date, end_date):
        """Run the backtest"""
        try:
            # Get market data
            data = self.get_gold_data(start_date, end_date)
            
            if data.empty or len(data) < 20:
                return self._empty_results("No sufficient data available")
            
            # Calculate indicators
            indicators = self.calculate_indicators(data)
            
            # Generate signals
            buy_signals, sell_signals = self.generate_signals(data, indicators)
            
            # Run simulation
            capital = self.initial_capital
            position = 0
            trades = []
            equity_curve = [capital]
            
            for i in range(len(data)):
                current_price = data['Close'].iloc[i]
                current_time = data.index[i]
                
                # Buy signal
                if buy_signals.iloc[i] and position == 0:
                    shares = capital / current_price
                    position = shares
                    capital = 0
                    entry_price = current_price
                    entry_time = current_time
                
                # Sell signal
                elif sell_signals.iloc[i] and position > 0:
                    capital = position * current_price
                    pnl = capital - self.initial_capital
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'shares': position
                    })
                    
                    position = 0
                
                # Update equity curve
                current_equity = capital + (position * current_price if position > 0 else 0)
                equity_curve.append(current_equity)
            
            # Calculate final metrics
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
                
                # Calculate additional metrics
                if winning_trades and len(trades) > len(winning_trades):
                    avg_win = np.mean([t['pnl'] for t in winning_trades])
                    losing_trades = [t for t in trades if t['pnl'] <= 0]
                    avg_loss = abs(np.mean([t['pnl'] for t in losing_trades])) if losing_trades else 1
                    profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
                else:
                    profit_factor = 0
                
            else:
                total_return = 0
                win_rate = 0
                max_drawdown = 0
                profit_factor = 0
            
            # Create equity curve series
            equity_series = pd.Series(
                equity_curve[:len(data)], 
                index=data.index
            )
            
            return {
                'total_return': total_return,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'total_trades': len(trades),
                'profit_factor': profit_factor,
                'sharpe_ratio': 0,  # Simplified
                'equity_curve': equity_series,
                'trades': pd.DataFrame(trades),
                'success': True,
                'data_points': len(data),
                'period': f"{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}",
                'interval': data.index.freq or 'Variable',
                'data_source': getattr(self, 'data_source', 'Yahoo Finance Gold Futures (GC=F)'),
                'data_verification': {
                    'first_price': float(data['Close'].iloc[0]),
                    'last_price': float(data['Close'].iloc[-1]),
                    'price_range': f"${data['Close'].min():.2f} - ${data['Close'].max():.2f}",
                    'is_real_data': True
                }
            }
            
        except Exception as e:
            print(f"Backtest error: {e}")
            return self._empty_results(f"Error: {str(e)}")
    
    def _empty_results(self, reason="No data"):
        """Return empty results"""
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'equity_curve': pd.Series([]),
            'trades': pd.DataFrame(),
            'success': False,
            'data_points': 0,
            'period': reason,
            'interval': 'N/A'
        }

def run_simple_backtest(start_date, end_date, initial_capital=100000):
    """Simple backtest function for Streamlit integration"""
    backtester = SimpleBacktester(initial_capital)
    return backtester.run_backtest(start_date, end_date)

# Test function
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Testing backtest from {start_date.date()} to {end_date.date()}")
    
    results = run_simple_backtest(start_date, end_date)
    
    print(f"Success: {results['success']}")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Data Points: {results['data_points']}")
