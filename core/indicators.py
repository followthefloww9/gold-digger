"""
Gold Digger AI Bot - Smart Money Concepts Indicators
Technical analysis indicators for XAU/USD trading strategy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMCIndicators:
    """
    Smart Money Concepts indicators for institutional trading analysis
    Implements Order Blocks, Break of Structure, Liquidity Grabs, and Fair Value Gaps
    """
    
    def __init__(self):
        """Initialize SMC indicators"""
        logger.info("SMCIndicators initialized")
    
    def add_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add basic technical indicators to the dataframe
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicators
        """
        try:
            if df is None or len(df) == 0:
                logger.warning("⚠️ Empty DataFrame provided to add_basic_indicators")
                return df

            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close']
            for col in required_cols:
                if col not in df.columns:
                    logger.warning(f"⚠️ Missing column {col}, using Close price")
                    df[col] = df.get('Close', 0)

            # Calculate VWAP (Volume Weighted Average Price)
            df['VWAP'] = self._calculate_vwap(df)

            # Calculate EMAs with minimum period checks
            if len(df) >= 21:
                df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            else:
                df['EMA_21'] = df['Close']

            if len(df) >= 50:
                df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            else:
                df['EMA_50'] = df['Close']

            if len(df) >= 200:
                df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
            else:
                df['EMA_200'] = df['Close']

            # Calculate RSI
            df['RSI'] = self._calculate_rsi(df['Close'], period=14)

            # Calculate ATR (Average True Range)
            df['ATR'] = self._calculate_atr(df, period=14)

            logger.info("Basic indicators added successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error adding basic indicators: {str(e)}")
            return df
    
    def _calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        try:
            if df is None or len(df) == 0:
                return pd.Series(dtype=float)

            typical_price = (df['High'] + df['Low'] + df['Close']) / 3

            # Ensure volume is a Series with proper index
            if 'Volume' in df.columns:
                volume = df['Volume']
            else:
                volume = pd.Series([1000] * len(df), index=df.index)

            # Ensure volume is numeric
            volume = pd.to_numeric(volume, errors='coerce').fillna(1000)

            cumulative_volume = volume.cumsum()
            cumulative_price_volume = (typical_price * volume).cumsum()

            # Avoid division by zero
            vwap = cumulative_price_volume / cumulative_volume.replace(0, 1)
            return vwap.fillna(typical_price)
            
        except Exception as e:
            logger.error(f"Error calculating VWAP: {str(e)}")
            return df['Close']  # Fallback to close price
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(50)  # Neutral RSI for NaN values
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([50] * len(prices), index=prices.index)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            return atr.fillna(true_range)
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return pd.Series([1.0] * len(df), index=df.index)
    
    def get_session_levels(self, df: pd.DataFrame, session_type: str = 'ALL') -> Dict[str, float]:
        """
        Identify session-based liquidity levels
        
        Args:
            df: DataFrame with OHLCV data
            session_type: 'ASIAN', 'LONDON', 'NEW_YORK', or 'ALL'
            
        Returns:
            Dictionary with session levels
        """
        try:
            # For demo purposes, calculate recent highs and lows
            recent_data = df.tail(50)  # Last 50 candles
            
            levels = {
                'session_high': recent_data['High'].max(),
                'session_low': recent_data['Low'].min(),
                'previous_day_high': recent_data['High'].iloc[-24:].max() if len(recent_data) >= 24 else recent_data['High'].max(),
                'previous_day_low': recent_data['Low'].iloc[-24:].min() if len(recent_data) >= 24 else recent_data['Low'].min(),
                'weekly_high': recent_data['High'].max(),
                'weekly_low': recent_data['Low'].min()
            }
            
            logger.info(f"Session levels calculated for {session_type}")
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating session levels: {str(e)}")
            return {
                'session_high': df['High'].iloc[-1] if not df.empty else 2000.0,
                'session_low': df['Low'].iloc[-1] if not df.empty else 1900.0,
                'previous_day_high': df['High'].iloc[-1] if not df.empty else 2000.0,
                'previous_day_low': df['Low'].iloc[-1] if not df.empty else 1900.0,
                'weekly_high': df['High'].iloc[-1] if not df.empty else 2000.0,
                'weekly_low': df['Low'].iloc[-1] if not df.empty else 1900.0
            }
    
    def detect_order_blocks(self, df: pd.DataFrame, timeframe: str = 'M15') -> List[Dict]:
        """
        Detect Order Blocks (institutional buying/selling zones)
        
        Args:
            df: DataFrame with OHLCV data
            timeframe: Chart timeframe
            
        Returns:
            List of order block dictionaries
        """
        try:
            order_blocks = []
            
            if len(df) < 20:
                return order_blocks
            
            # Simple order block detection based on significant price moves
            for i in range(10, len(df) - 5):
                current_candle = df.iloc[i]
                
                # Look for strong bullish moves (potential bullish OB)
                if (current_candle['Close'] > current_candle['Open'] and
                    current_candle['High'] - current_candle['Low'] > df['ATR'].iloc[i] * 1.5):
                    
                    order_blocks.append({
                        'type': 'bullish',
                        'top': current_candle['High'],
                        'bottom': current_candle['Low'],
                        'timestamp': df.index[i],
                        'strength': min(10, int((current_candle['High'] - current_candle['Low']) / df['ATR'].iloc[i] * 2)),
                        'status': 'fresh',
                        'timeframe': timeframe
                    })
                
                # Look for strong bearish moves (potential bearish OB)
                elif (current_candle['Close'] < current_candle['Open'] and
                      current_candle['High'] - current_candle['Low'] > df['ATR'].iloc[i] * 1.5):
                    
                    order_blocks.append({
                        'type': 'bearish',
                        'top': current_candle['High'],
                        'bottom': current_candle['Low'],
                        'timestamp': df.index[i],
                        'strength': min(10, int((current_candle['High'] - current_candle['Low']) / df['ATR'].iloc[i] * 2)),
                        'status': 'fresh',
                        'timeframe': timeframe
                    })
            
            # Keep only the most recent and strongest order blocks
            order_blocks = sorted(order_blocks, key=lambda x: (x['timestamp'], x['strength']), reverse=True)[:5]
            
            logger.info(f"Detected {len(order_blocks)} order blocks")
            return order_blocks
            
        except Exception as e:
            logger.error(f"Error detecting order blocks: {str(e)}")
            return []
    
    def detect_break_of_structure(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Detect Break of Structure (BOS) - trend changes
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with BOS information
        """
        try:
            if len(df) < 20:
                return {'bos_detected': False, 'direction': 'NEUTRAL', 'strength': 0}
            
            # Simple BOS detection based on recent highs and lows
            recent_data = df.tail(20)
            
            # Check for higher highs and higher lows (bullish BOS)
            recent_highs = recent_data['High'].rolling(window=5).max()
            recent_lows = recent_data['Low'].rolling(window=5).min()
            
            # Bullish BOS: Recent high breaks previous high
            if recent_highs.iloc[-1] > recent_highs.iloc[-10:-5].max():
                return {
                    'bos_detected': True,
                    'direction': 'BULLISH',
                    'strength': 7,
                    'break_price': recent_highs.iloc[-1],
                    'timestamp': df.index[-1]
                }
            
            # Bearish BOS: Recent low breaks previous low
            elif recent_lows.iloc[-1] < recent_lows.iloc[-10:-5].min():
                return {
                    'bos_detected': True,
                    'direction': 'BEARISH',
                    'strength': 7,
                    'break_price': recent_lows.iloc[-1],
                    'timestamp': df.index[-1]
                }
            
            return {'bos_detected': False, 'direction': 'NEUTRAL', 'strength': 0}
            
        except Exception as e:
            logger.error(f"Error detecting BOS: {str(e)}")
            return {'bos_detected': False, 'direction': 'NEUTRAL', 'strength': 0}
    
    def detect_liquidity_grabs(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect liquidity grabs (stop hunts)
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of liquidity grab events
        """
        try:
            liquidity_grabs = []
            
            if len(df) < 10:
                return liquidity_grabs
            
            # Look for spikes that quickly reverse
            for i in range(5, len(df) - 2):
                current = df.iloc[i]
                previous = df.iloc[i-1]
                next_candle = df.iloc[i+1]
                
                # Upward spike that reverses (liquidity grab above)
                if (current['High'] > previous['High'] * 1.002 and  # 0.2% spike
                    next_candle['Close'] < current['Open']):
                    
                    liquidity_grabs.append({
                        'type': 'upward_grab',
                        'price': current['High'],
                        'timestamp': df.index[i],
                        'strength': 6
                    })
                
                # Downward spike that reverses (liquidity grab below)
                elif (current['Low'] < previous['Low'] * 0.998 and  # 0.2% spike down
                      next_candle['Close'] > current['Open']):
                    
                    liquidity_grabs.append({
                        'type': 'downward_grab',
                        'price': current['Low'],
                        'timestamp': df.index[i],
                        'strength': 6
                    })
            
            # Keep only recent grabs
            liquidity_grabs = liquidity_grabs[-3:]  # Last 3 grabs
            
            logger.info(f"Detected {len(liquidity_grabs)} liquidity grabs")
            return liquidity_grabs
            
        except Exception as e:
            logger.error(f"Error detecting liquidity grabs: {str(e)}")
            return []
    
    def analyze_market_structure(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Comprehensive market structure analysis

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Complete market structure analysis
        """
        try:
            if df is None or len(df) == 0:
                logger.warning("⚠️ Empty DataFrame provided to analyze_market_structure")
                return {
                    'current_price': 0.0,
                    'trend': 'UNKNOWN',
                    'order_blocks': [],
                    'liquidity_zones': [],
                    'session_levels': {},
                    'setup_quality': 0,
                    'error': 'No market data available'
                }

            # Add basic indicators
            df_with_indicators = self.add_basic_indicators(df.copy())
            
            # Get all SMC components
            session_levels = self.get_session_levels(df_with_indicators)
            order_blocks = self.detect_order_blocks(df_with_indicators)
            bos_analysis = self.detect_break_of_structure(df_with_indicators)
            liquidity_grabs = self.detect_liquidity_grabs(df_with_indicators)
            
            # Determine overall trend (per strategy.md: EMA 50/200 confluence)
            current_price = df_with_indicators['Close'].iloc[-1]
            ema_21 = df_with_indicators['EMA_21'].iloc[-1]
            ema_50 = df_with_indicators['EMA_50'].iloc[-1]
            ema_200 = df_with_indicators['EMA_200'].iloc[-1]

            # Enhanced trend analysis with EMA 50/200 confluence (strategy.md requirement)
            if current_price > ema_50 > ema_200:
                trend = 'BULLISH'
            elif current_price < ema_50 < ema_200:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
            
            analysis = {
                'timestamp': df.index[-1],
                'current_price': current_price,
                'trend': trend,
                'session_levels': session_levels,
                'order_blocks': order_blocks,
                'bos_analysis': bos_analysis,
                'liquidity_grabs': liquidity_grabs,
                'indicators': {
                    'vwap': df_with_indicators['VWAP'].iloc[-1],
                    'ema_21': ema_21,
                    'ema_50': ema_50,
                    'ema_200': ema_200,  # Added per strategy.md
                    'rsi': df_with_indicators['RSI'].iloc[-1],
                    'atr': df_with_indicators['ATR'].iloc[-1]
                }
            }
            
            logger.info("Market structure analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {str(e)}")
            return {
                'timestamp': df.index[-1] if not df.empty else pd.Timestamp.now(),
                'current_price': df['Close'].iloc[-1] if not df.empty else 1987.0,
                'trend': 'NEUTRAL',
                'session_levels': {},
                'order_blocks': [],
                'bos_analysis': {'bos_detected': False, 'direction': 'NEUTRAL'},
                'liquidity_grabs': [],
                'indicators': {}
            }

# Test function
def test_indicators():
    """Test SMC indicators with sample data"""
    print("🔍 Testing SMC Indicators...")
    
    # Create sample data
    dates = pd.date_range(start='2025-01-01', periods=100, freq='5T')
    np.random.seed(42)  # For reproducible results
    
    # Generate realistic XAUUSD price data
    base_price = 1987.0
    prices = [base_price]
    
    for i in range(99):
        change = np.random.normal(0, 0.5)
        new_price = prices[-1] + change
        prices.append(new_price)
    
    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        open_price = price
        high_price = open_price + abs(np.random.normal(0, 0.3))
        low_price = open_price - abs(np.random.normal(0, 0.3))
        close_price = open_price + np.random.normal(0, 0.2)
        volume = np.random.randint(100, 1000)
        
        data.append({
            'Open': open_price,
            'High': high_price,
            'Low': low_price,
            'Close': close_price,
            'Volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    
    # Test indicators
    smc = SMCIndicators()
    analysis = smc.analyze_market_structure(df)
    
    print("✅ SMC Indicators Test Results:")
    print(f"   Current Price: ${analysis['current_price']:.2f}")
    print(f"   Trend: {analysis['trend']}")
    print(f"   Order Blocks: {len(analysis['order_blocks'])}")
    print(f"   BOS Detected: {analysis['bos_analysis']['bos_detected']}")
    print(f"   Liquidity Grabs: {len(analysis['liquidity_grabs'])}")
    print(f"   VWAP: ${analysis['indicators'].get('vwap', 0):.2f}")
    print(f"   RSI: {analysis['indicators'].get('rsi', 0):.1f}")
    
    return True

if __name__ == "__main__":
    test_indicators()
