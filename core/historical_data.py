"""
Historical Data Fetcher for Gold Digger AI Bot
Provides comprehensive historical market data for backtesting
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
import requests
import time

logger = logging.getLogger(__name__)

class HistoricalDataFetcher:
    """
    Comprehensive historical data fetcher for backtesting
    Supports multiple data sources and timeframes
    """
    
    def __init__(self):
        """Initialize historical data fetcher"""
        self.gold_symbols = {
            'yahoo': 'GC=F',  # Gold Futures
            'yahoo_spot': 'GOLD',  # Gold Spot (if available)
            'yahoo_etf': 'GLD'  # Gold ETF as backup
        }
        
        logger.info("📊 Historical Data Fetcher initialized")
    
    def get_gold_historical_data(self, start_date: datetime, end_date: datetime, 
                                interval: str = '5m') -> Optional[pd.DataFrame]:
        """
        Get comprehensive historical gold data
        
        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1m', '5m', '15m', '1h', '1d')
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            logger.info(f"📊 Fetching historical gold data: {start_date.date()} to {end_date.date()}")
            
            # Try multiple approaches for best data coverage
            data = None
            
            # Method 1: Yahoo Finance Gold Futures (GC=F)
            data = self._fetch_yahoo_data('GC=F', start_date, end_date, interval)
            
            if data is None or len(data) < 10:
                logger.warning("⚠️ Gold futures data insufficient, trying Gold ETF")
                # Method 2: Gold ETF (GLD) as backup
                data = self._fetch_yahoo_data('GLD', start_date, end_date, interval)

            if data is None or len(data) < 10:
                logger.error("❌ No real market data available for the requested period")
                logger.error("❌ Synthetic data disabled - only real market data allowed")
                return None
            
            if data is not None and len(data) > 0:
                # Ensure proper format for backtesting
                data = self._format_for_backtesting(data)
                logger.info(f"✅ Historical data retrieved: {len(data)} candles")
                return data
            else:
                logger.error("❌ All historical data methods failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Historical data error: {e}")
            return None
    
    def _fetch_yahoo_data(self, symbol: str, start_date: datetime, 
                         end_date: datetime, interval: str) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance"""
        try:
            logger.info(f"📊 Fetching {symbol} data from Yahoo Finance")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Adjust interval for Yahoo Finance API
            yf_interval = self._convert_interval_to_yahoo(interval)
            
            # Fetch historical data
            data = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval=yf_interval,
                auto_adjust=True,
                prepost=True
            )
            
            if data is not None and len(data) > 0:
                logger.info(f"✅ Yahoo Finance data: {len(data)} candles for {symbol}")
                
                # Rename columns to match our format
                data = data.rename(columns={
                    'Open': 'Open',
                    'High': 'High', 
                    'Low': 'Low',
                    'Close': 'Close',
                    'Volume': 'Volume'
                })
                
                # Add metadata
                data['Symbol'] = 'XAUUSD'
                data['Timeframe'] = interval
                data['Source'] = f'Yahoo Finance ({symbol})'
                
                return data
            else:
                logger.warning(f"⚠️ No data from Yahoo Finance for {symbol}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Yahoo Finance error for {symbol}: {e}")
            return None
    
    def _convert_interval_to_yahoo(self, interval: str) -> str:
        """Convert our interval format to Yahoo Finance format"""
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '1d': '1d',
            'M1': '1m',
            'M5': '5m',
            'M15': '15m',
            'M30': '30m',
            'H1': '1h',
            'D1': '1d'
        }
        return interval_map.get(interval, '5m')
    
    def _generate_synthetic_gold_data(self, start_date: datetime, end_date: datetime, 
                                    interval: str) -> pd.DataFrame:
        """Generate realistic synthetic gold data for testing"""
        try:
            logger.info("📊 Generating synthetic gold data for testing")
            
            # Calculate time delta based on interval
            if interval in ['1m', 'M1']:
                freq = '1min'
            elif interval in ['5m', 'M5']:
                freq = '5min'
            elif interval in ['15m', 'M15']:
                freq = '15min'
            elif interval in ['1h', 'H1']:
                freq = '1H'
            else:
                freq = '5min'  # Default
            
            # Create date range
            date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            
            # Generate realistic gold price movement
            base_price = 3340.0  # Current gold price level
            num_points = len(date_range)
            
            # Create realistic price series with trends and volatility
            np.random.seed(42)  # For reproducible results
            
            # Generate price movements
            returns = np.random.normal(0, 0.001, num_points)  # 0.1% volatility
            trend = np.linspace(-0.02, 0.02, num_points)  # Slight trend
            cyclical = 0.01 * np.sin(np.linspace(0, 4*np.pi, num_points))  # Cyclical pattern
            
            # Combine components
            price_changes = returns + trend + cyclical
            prices = base_price * (1 + price_changes).cumprod()
            
            # Generate OHLC data
            data = []
            for i, (timestamp, close_price) in enumerate(zip(date_range, prices)):
                # Generate realistic OHLC from close price
                volatility = abs(np.random.normal(0, 0.002))  # Intrabar volatility
                
                open_price = close_price * (1 + np.random.normal(0, 0.0005))
                high_price = max(open_price, close_price) * (1 + volatility)
                low_price = min(open_price, close_price) * (1 - volatility)
                volume = np.random.randint(1000, 5000)
                
                data.append({
                    'Time': timestamp,
                    'Open': round(open_price, 2),
                    'High': round(high_price, 2),
                    'Low': round(low_price, 2),
                    'Close': round(close_price, 2),
                    'Volume': volume,
                    'Symbol': 'XAUUSD',
                    'Timeframe': interval,
                    'Source': 'Synthetic Data'
                })
            
            df = pd.DataFrame(data)
            df.set_index('Time', inplace=True)
            
            logger.info(f"✅ Generated {len(df)} synthetic candles")
            return df
            
        except Exception as e:
            logger.error(f"❌ Synthetic data generation error: {e}")
            return None
    
    def _format_for_backtesting(self, data: pd.DataFrame) -> pd.DataFrame:
        """Format data for backtesting engine compatibility"""
        try:
            # Ensure required columns exist
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    logger.warning(f"⚠️ Missing column {col}, using Close price")
                    data[col] = data['Close'] if 'Close' in data.columns else 3340.0
            
            # Ensure proper data types
            for col in required_columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Remove any NaN values
            data = data.dropna()
            
            # Ensure datetime index
            if not isinstance(data.index, pd.DatetimeIndex):
                if 'Time' in data.columns:
                    data.set_index('Time', inplace=True)
                else:
                    data.index = pd.to_datetime(data.index)
            
            # Add metadata if missing
            if 'Symbol' not in data.columns:
                data['Symbol'] = 'XAUUSD'
            if 'Timeframe' not in data.columns:
                data['Timeframe'] = 'M5'
            
            # Sort by time
            data = data.sort_index()
            
            logger.info(f"✅ Data formatted for backtesting: {len(data)} candles")
            return data
            
        except Exception as e:
            logger.error(f"❌ Data formatting error: {e}")
            return data
    
    def get_available_date_range(self) -> Tuple[datetime, datetime]:
        """Get the available date range for historical data"""
        try:
            # For Yahoo Finance, we can typically get several years of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # 1 year back
            
            return start_date, end_date
            
        except Exception as e:
            logger.error(f"❌ Error getting date range: {e}")
            # Fallback to last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            return start_date, end_date
    
    def test_data_availability(self) -> Dict:
        """Test data availability from different sources"""
        try:
            logger.info("🔍 Testing historical data availability")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            results = {}
            
            # Test Yahoo Finance Gold Futures
            gc_data = self._fetch_yahoo_data('GC=F', start_date, end_date, '1d')
            results['gold_futures'] = {
                'available': gc_data is not None and len(gc_data) > 0,
                'candles': len(gc_data) if gc_data is not None else 0,
                'symbol': 'GC=F'
            }
            
            # Test Gold ETF
            gld_data = self._fetch_yahoo_data('GLD', start_date, end_date, '1d')
            results['gold_etf'] = {
                'available': gld_data is not None and len(gld_data) > 0,
                'candles': len(gld_data) if gld_data is not None else 0,
                'symbol': 'GLD'
            }
            
            # Real data only - no synthetic fallback
            results['real_data_only'] = {
                'policy': 'Only real market data allowed',
                'synthetic_disabled': True,
                'fallback': 'None - real data required'
            }
            
            logger.info(f"✅ Data availability test completed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Data availability test error: {e}")
            return {}
