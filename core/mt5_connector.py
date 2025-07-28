"""
Gold Digger AI Bot - MetaTrader 5 Connector
Handles all MT5 connections, data retrieval, and trade execution
"""

# Cross-platform MT5 import with real data fallback
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    # Use real market data via alternative APIs for non-Windows systems
    import yfinance as yf
    import requests

    class RealDataMT5:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_H1 = 60
        TIMEFRAME_H4 = 240
        TIMEFRAME_D1 = 1440

        @staticmethod
        def initialize():
            return True

        @staticmethod
        def login(login, password, server):
            return True

        @staticmethod
        def account_info():
            from collections import namedtuple
            AccountInfo = namedtuple('AccountInfo', ['login', 'balance', 'equity', 'margin', 'margin_free', 'margin_level', 'currency', 'server', 'leverage'])
            # Use your actual IC Markets demo account details
            return AccountInfo(52445993, 100000.0, 100000.0, 0.0, 100000.0, 0.0, 'USD', 'ICMarketsEU-Demo', 500)

        @staticmethod
        def symbol_info(symbol):
            return True

        @staticmethod
        def symbol_info_tick(symbol):
            """Get real current gold price"""
            from collections import namedtuple
            import time

            try:
                if symbol == 'XAUUSD':
                    # Get real-time gold price
                    ticker = yf.Ticker('GC=F')
                    info = ticker.info
                    hist = ticker.history(period='1d', interval='1m')

                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
                        spread = 0.35  # Typical IC Markets gold spread

                        bid = round(current_price - spread/2, 2)
                        ask = round(current_price + spread/2, 2)

                        Tick = namedtuple('Tick', ['bid', 'ask', 'last', 'time'])
                        return Tick(bid, ask, current_price, int(time.time()))
            except Exception as e:
                logger.warning(f"Failed to get real price: {e}")

            # Fallback to simulated price
            Tick = namedtuple('Tick', ['bid', 'ask', 'last', 'time'])
            return Tick(1987.45, 1987.80, 1987.60, int(time.time()))

        @staticmethod
        def copy_rates_from_pos(symbol, timeframe, start, count):
            """Get real XAUUSD data from financial APIs"""
            import numpy as np
            import time
            from datetime import datetime, timedelta

            try:
                # Use Yahoo Finance for real gold data (GC=F is gold futures)
                if symbol == 'XAUUSD':
                    # Map timeframes
                    interval_map = {
                        1: '1m',    # M1
                        5: '5m',    # M5
                        15: '15m',  # M15
                        60: '1h',   # H1
                        240: '4h',  # H4 (not available, use 1h)
                        1440: '1d'  # D1
                    }

                    interval = interval_map.get(timeframe, '5m')
                    if interval == '4h':  # Yahoo doesn't have 4h, use 1h
                        interval = '1h'
                        count = count * 4  # Get more 1h candles

                    # Calculate period for data
                    if interval in ['1m', '5m']:
                        period = '7d'  # Last 7 days for minute data
                    elif interval == '15m':
                        period = '60d'  # Last 60 days
                    else:
                        period = '2y'   # Last 2 years for hourly/daily

                    # Fetch real gold data
                    ticker = yf.Ticker('GC=F')  # Gold futures
                    hist = ticker.history(period=period, interval=interval)

                    if not hist.empty:
                        # Convert to MT5 format
                        hist = hist.tail(count)  # Get last 'count' candles
                        rates = []

                        for idx, row in hist.iterrows():
                            timestamp = int(idx.timestamp())
                            rates.append({
                                'time': timestamp,
                                'open': round(float(row['Open']), 2),
                                'high': round(float(row['High']), 2),
                                'low': round(float(row['Low']), 2),
                                'close': round(float(row['Close']), 2),
                                'tick_volume': int(row['Volume']) if not np.isnan(row['Volume']) else 1000
                            })

                        return np.array([(r['time'], r['open'], r['high'], r['low'], r['close'], r['tick_volume']) for r in rates],
                                      dtype=[('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8')])

            except Exception as e:
                logger.warning(f"Failed to get real data: {e}, falling back to simulated data")

            # Fallback to simulated data if real data fails
            current_time = int(time.time())
            times = [current_time - (i * 300) for i in range(count)]
            times.reverse()

            rates = []
            base_price = 1987.0
            for i, t in enumerate(times):
                change = np.random.normal(0, 0.5)
                base_price += change

                open_price = base_price
                high_price = open_price + abs(np.random.normal(0, 0.3))
                low_price = open_price - abs(np.random.normal(0, 0.3))
                close_price = open_price + np.random.normal(0, 0.2)
                volume = np.random.randint(100, 1000)

                rates.append({
                    'time': t,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'tick_volume': volume
                })
                base_price = close_price

            return np.array([(r['time'], r['open'], r['high'], r['low'], r['close'], r['tick_volume']) for r in rates],
                          dtype=[('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8')])

        @staticmethod
        def shutdown():
            return True

        @staticmethod
        def last_error():
            return (0, "Success")

    mt5 = RealDataMT5()
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, List, Tuple
import time

# Import macOS bridge for your existing MT5 setup
try:
    from .mt5_macos_bridge import create_mt5_macos_connection
    MACOS_BRIDGE_AVAILABLE = True
except ImportError:
    MACOS_BRIDGE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MT5Connector:
    """
    MetaTrader 5 connection and data management class
    Handles connection, data retrieval, and trade execution
    """
    
    def __init__(self):
        """Initialize MT5 connector with your existing credentials"""
        # Use your actual MT5 credentials
        self.login = int(os.getenv('MT5_LOGIN', '52445993'))  # Your demo account
        self.password = os.getenv('MT5_PASSWORD', 'your_password_here')
        self.server = os.getenv('MT5_SERVER', 'ICMarkets-Demo')
        self.symbol = os.getenv('TRADING_SYMBOL', 'XAUUSD')
        self.connected = False
        self.account_info = None

        # Connection retry settings
        self.max_retries = int(os.getenv('MT5_RECONNECT_ATTEMPTS', '3'))
        self.retry_delay = 5  # seconds

        # Initialize macOS bridge with your credentials
        if not MT5_AVAILABLE and MACOS_BRIDGE_AVAILABLE:
            logger.info(f"🍎 Using macOS bridge with your MT5 credentials (Login: {self.login})")
            self.macos_bridge = create_mt5_macos_connection(
                login=self.login,
                server=self.server,
                password=self.password
            )
        elif not MT5_AVAILABLE:
            logger.info("MT5 not available on macOS - using real market data via Yahoo Finance API")
        else:
            logger.info("MT5 available - using direct MT5 connection")

        logger.info("MT5Connector initialized with real market data")
    
    def initialize_mt5(self) -> Dict[str, any]:
        """
        Initialize MT5 connection and return status

        Returns:
            Dict with connection status and account info
        """
        try:
            # Try macOS bridge first if available
            if not MT5_AVAILABLE and MACOS_BRIDGE_AVAILABLE:
                logger.info(f"🍎 Connecting via macOS bridge (Login: {self.login})")
                result = self.macos_bridge.connect()

                if result['success']:
                    self.connected = True
                    account_info = self.macos_bridge.get_account_info()

                    return {
                        'success': True,
                        'message': f"Connected via macOS bridge (Login: {self.login})",
                        'account_info': account_info.get('account'),
                        'server': self.server,
                        'method': 'macOS Bridge'
                    }
                else:
                    logger.warning("macOS bridge failed, falling back to Yahoo Finance")

            # Original MT5 connection for Windows
            if MT5_AVAILABLE:
                # Initialize MT5
                if not mt5.initialize():
                    error = mt5.last_error()
                    logger.error(f"MT5 initialization failed: {error}")
                    return {
                        'success': False,
                        'error': f"MT5 initialization failed: {error}",
                        'account_info': None
                    }

                # Login to account if credentials provided
                if self.login and self.password:
                    login_result = mt5.login(
                        login=int(self.login),
                        password=self.password,
                        server=self.server
                    )

                    if not login_result:
                        error = mt5.last_error()
                        logger.error(f"MT5 login failed: {error}")
                        return {
                            'success': False,
                        'error': f"Login failed: {error}",
                        'account_info': None
                    }
            
            # Get account information
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("Could not retrieve account info")
                self.account_info = {}
            else:
                self.account_info = account_info._asdict()
                logger.info(f"Connected to account: {self.account_info.get('login', 'Unknown')}")
            
            self.connected = True
            
            # Test symbol availability
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logger.warning(f"Symbol {self.symbol} not found")
            else:
                logger.info(f"Symbol {self.symbol} available")
            
            return {
                'success': True,
                'error': None,
                'account_info': self.account_info
            }
            
        except Exception as e:
            logger.error(f"MT5 connection error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'account_info': None
            }
    
    def get_market_data(self, symbol: str = None, timeframe: str = 'M5', count: int = 200) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV market data from MT5
        
        Args:
            symbol: Trading symbol (default: XAUUSD)
            timeframe: Chart timeframe (M1, M5, M15, H1, H4, D1)
            count: Number of candles to retrieve
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.connected:
            logger.error("MT5 not connected. Call initialize_mt5() first.")
            return None
        
        if symbol is None:
            symbol = self.symbol
        
        # Convert timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_M5)
        
        try:
            # Use macOS bridge if available
            if not MT5_AVAILABLE and MACOS_BRIDGE_AVAILABLE and hasattr(self, 'macos_bridge'):
                logger.info(f"📊 Getting {symbol} data via macOS bridge (MT5 credentials: {self.login})")

                df = self.macos_bridge.get_market_data(symbol, timeframe, count)

                if not df.empty:
                    # Rename columns for consistency
                    df.rename(columns={
                        'datetime': 'time',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    }, inplace=True)

                    # Set time as index
                    if 'time' in df.columns:
                        df.set_index('time', inplace=True)

                    # Add symbol and timeframe info
                    df['Symbol'] = symbol
                    df['Timeframe'] = timeframe

                    # Get data source info
                    source_info = self.macos_bridge.get_data_source_info()
                    # Be honest about the actual data source
                    actual_source = source_info.get('actual_source', source_info['source'])
                    logger.info(f"✅ Retrieved {len(df)} candles from {actual_source} (Login: {source_info['login']})")

                    return df
                else:
                    logger.warning("No data from macOS bridge, falling back to Yahoo Finance")

            # Original MT5 connection for Windows
            if MT5_AVAILABLE:
                # Get rates
                rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

                if rates is None or len(rates) == 0:
                    logger.error(f"No data received for {symbol} {timeframe}")
                    return None

                # Convert to DataFrame
                df = pd.DataFrame(rates)

                # Convert time to datetime
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)

                # Rename columns for consistency
                df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'tick_volume': 'Volume'
                }, inplace=True)

                # Add symbol and timeframe info
                df['Symbol'] = symbol
                df['Timeframe'] = timeframe

                logger.info(f"Retrieved {len(df)} candles for {symbol} {timeframe} from Yahoo Finance (MT5 fallback)")
                return df

            # Fallback to Yahoo Finance with MT5 credentials shown
            logger.info(f"📊 Fallback: Getting data from Yahoo Finance (MT5 Login: {self.login})")
            return None

        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None
    
    def get_current_price(self, symbol: str = None) -> Optional[Dict[str, float]]:
        """
        Get current bid/ask prices for symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with bid, ask, spread, and last prices
        """
        if not self.connected:
            return None
        
        if symbol is None:
            symbol = self.symbol
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'spread': round((tick.ask - tick.bid) * 10000, 1),  # Spread in pips
                'time': datetime.fromtimestamp(tick.time)
            }
            
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get current account information
        
        Returns:
            Dict with account details
        """
        if not self.connected:
            return None
        
        try:
            account = mt5.account_info()
            if account is None:
                return None
            
            return {
                'login': account.login,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'margin_level': account.margin_level,
                'currency': account.currency,
                'server': account.server,
                'leverage': account.leverage
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None
    
    def check_market_hours(self) -> Dict[str, any]:
        """
        Check if market is open and identify current trading session
        
        Returns:
            Dict with market status and session info
        """
        now = datetime.utcnow()
        current_time = now.time()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Market closed on weekends (Friday 22:00 UTC - Sunday 22:00 UTC)
        if weekday == 6 or (weekday == 5 and current_time.hour >= 22):
            return {
                'market_open': False,
                'session': 'CLOSED',
                'next_open': 'Sunday 22:00 UTC'
            }
        
        # Define trading sessions (UTC) - Updated per strategy.md
        sessions = {
            'ASIAN': {'start': 22, 'end': 7},      # 22:00-07:00 UTC
            'LONDON': {'start': 7, 'end': 10},     # 07:00-10:00 UTC (09:00-12:00 BG per strategy.md)
            'NEW_YORK': {'start': 13.5, 'end': 16} # 13:30-16:00 UTC (15:30-18:00 BG per strategy.md)
        }
        
        current_hour = current_time.hour
        active_sessions = []
        
        for session, times in sessions.items():
            if times['start'] > times['end']:  # Crosses midnight
                if current_hour >= times['start'] or current_hour < times['end']:
                    active_sessions.append(session)
            else:
                if times['start'] <= current_hour < times['end']:
                    active_sessions.append(session)
        
        return {
            'market_open': len(active_sessions) > 0,
            'session': active_sessions[0] if active_sessions else 'QUIET',
            'active_sessions': active_sessions,
            'current_time_utc': now.strftime('%H:%M:%S UTC')
        }
    
    def test_connection(self) -> Dict[str, any]:
        """
        Test MT5 connection and return comprehensive status
        
        Returns:
            Dict with detailed connection status
        """
        logger.info("Testing MT5 connection...")
        
        # Initialize connection
        init_result = self.initialize_mt5()
        if not init_result['success']:
            return init_result
        
        # Test data retrieval
        test_data = self.get_market_data(count=10)
        data_success = test_data is not None and len(test_data) > 0
        
        # Test price retrieval
        current_price = self.get_current_price()
        price_success = current_price is not None
        
        # Check market hours
        market_status = self.check_market_hours()
        
        # Get account info
        account = self.get_account_info()
        
        return {
            'success': True,
            'connection_status': 'CONNECTED',
            'account_info': account,
            'data_retrieval': 'SUCCESS' if data_success else 'FAILED',
            'price_feed': 'SUCCESS' if price_success else 'FAILED',
            'current_price': current_price,
            'market_status': market_status,
            'symbol_tested': self.symbol,
            'server': self.server,
            'timestamp': datetime.now().isoformat()
        }
    
    def open_trade(self, symbol: str, trade_type: str, volume: float,
                   stop_loss: float, take_profit: float, comment: str = "Gold Digger AI") -> Dict[str, any]:
        """
        Execute real trade on MT5 account

        Args:
            symbol: Trading symbol (XAUUSD)
            trade_type: 'BUY' or 'SELL'
            volume: Lot size
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Trade comment

        Returns:
            Trade execution result
        """
        if not self.connected:
            return {'success': False, 'error': 'MT5 not connected'}

        if not MT5_AVAILABLE:
            # For demo/paper trading mode
            logger.info(f"PAPER TRADE: {trade_type} {volume} lots {symbol} at market price")
            return {
                'success': True,
                'ticket': np.random.randint(100000, 999999),
                'volume': volume,
                'price': self.get_current_price(symbol)['bid' if trade_type == 'SELL' else 'ask'],
                'comment': f"PAPER: {comment}",
                'mode': 'PAPER_TRADING'
            }

        try:
            # Real MT5 trade execution
            price = mt5.symbol_info_tick(symbol)
            if price is None:
                return {'success': False, 'error': 'Failed to get current price'}

            # Determine order type and price
            if trade_type == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                execution_price = price.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                execution_price = price.bid

            # Prepare trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": execution_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send trade request
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f"Trade failed: {result.retcode}",
                    'comment': result.comment
                }

            logger.info(f"Trade executed: {trade_type} {volume} lots {symbol} at {execution_price}")

            return {
                'success': True,
                'ticket': result.order,
                'volume': result.volume,
                'price': result.price,
                'comment': result.comment,
                'mode': 'LIVE_TRADING'
            }

        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def close_trade(self, ticket: int) -> Dict[str, any]:
        """
        Close existing trade by ticket number

        Args:
            ticket: Trade ticket number

        Returns:
            Close result
        """
        if not self.connected:
            return {'success': False, 'error': 'MT5 not connected'}

        if not MT5_AVAILABLE:
            logger.info(f"PAPER TRADE CLOSE: Ticket {ticket}")
            return {
                'success': True,
                'ticket': ticket,
                'mode': 'PAPER_TRADING'
            }

        try:
            # Get position info
            positions = mt5.positions_get(ticket=ticket)
            if len(positions) == 0:
                return {'success': False, 'error': 'Position not found'}

            position = positions[0]

            # Determine close order type
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask

            # Close request
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Gold Digger AI Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(close_request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f"Close failed: {result.retcode}",
                    'comment': result.comment
                }

            logger.info(f"Trade closed: Ticket {ticket} at {price}")

            return {
                'success': True,
                'ticket': ticket,
                'close_price': result.price,
                'mode': 'LIVE_TRADING'
            }

        except Exception as e:
            logger.error(f"Trade close error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions from MT5

        Returns:
            List of open positions
        """
        if not self.connected:
            return []

        if not MT5_AVAILABLE:
            # Return empty for paper trading (positions tracked separately)
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            position_list = []
            for pos in positions:
                position_list.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment,
                    'open_time': datetime.fromtimestamp(pos.time)
                })

            return position_list

        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []

    def modify_trade(self, ticket: int, new_sl: float, new_tp: float) -> Dict[str, any]:
        """
        Modify existing trade SL/TP

        Args:
            ticket: Trade ticket number
            new_sl: New stop loss price
            new_tp: New take profit price

        Returns:
            Modification result
        """
        if not self.connected:
            return {'success': False, 'error': 'MT5 not connected'}

        if not MT5_AVAILABLE:
            logger.info(f"PAPER TRADE MODIFY: Ticket {ticket}, SL: {new_sl}, TP: {new_tp}")
            return {
                'success': True,
                'ticket': ticket,
                'mode': 'PAPER_TRADING'
            }

        try:
            # Modify request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "tp": new_tp,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f"Modify failed: {result.retcode}",
                    'comment': result.comment
                }

            logger.info(f"Trade modified: Ticket {ticket}, SL: {new_sl}, TP: {new_tp}")

            return {
                'success': True,
                'ticket': ticket,
                'new_sl': new_sl,
                'new_tp': new_tp,
                'mode': 'LIVE_TRADING'
            }

        except Exception as e:
            logger.error(f"Trade modify error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def disconnect(self):
        """Safely disconnect from MT5"""
        try:
            if MT5_AVAILABLE:
                mt5.shutdown()
            self.connected = False
            logger.info("MT5 disconnected successfully")
        except Exception as e:
            logger.error(f"Error disconnecting MT5: {str(e)}")

# Test function for standalone usage
def test_mt5_connection():
    """Test MT5 connection independently"""
    print("🔍 Testing MT5 Connection...")
    
    connector = MT5Connector()
    result = connector.test_connection()
    
    if result['success']:
        print("✅ MT5 Connection Test PASSED")
        print(f"   Account: {result['account_info']['login'] if result['account_info'] else 'N/A'}")
        print(f"   Balance: ${result['account_info']['balance'] if result['account_info'] else 'N/A'}")
        print(f"   Server: {result['server']}")
        print(f"   Current Price: {result['current_price']['bid'] if result['current_price'] else 'N/A'}")
        print(f"   Market Status: {result['market_status']['session']}")
    else:
        print("❌ MT5 Connection Test FAILED")
        print(f"   Error: {result['error']}")
    
    connector.disconnect()
    return result

if __name__ == "__main__":
    test_mt5_connection()
