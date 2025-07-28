"""
Gold Digger AI Bot - Trading Engine
Main trading logic combining SMC analysis with AI decision making
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
import logging
from dotenv import load_dotenv

# Import MQL5 bridge for cross-platform trading
try:
    from .mql5_bridge import MQL5Bridge
    MQL5_AVAILABLE = True
except ImportError:
    MQL5_AVAILABLE = False

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingEngine:
    """
    Main trading engine that combines SMC indicators with AI validation
    Handles trade setup analysis, validation, and execution decisions
    """
    
    def __init__(self, use_mql5_bridge: bool = True):
        """Initialize trading engine"""
        self.min_risk_reward = 1.5  # Minimum risk-reward ratio
        self.max_risk_per_trade = 0.02  # Maximum 2% risk per trade
        self.max_daily_trades = 5  # Maximum trades per day

        # Initialize MQL5 bridge for cross-platform trading
        self.mql5_bridge = None
        self.use_mql5_bridge = use_mql5_bridge and MQL5_AVAILABLE

        if self.use_mql5_bridge:
            try:
                self.mql5_bridge = MQL5Bridge()
                logger.info("✅ MQL5 Bridge initialized for cross-platform trading")
            except Exception as e:
                logger.warning(f"⚠️ MQL5 Bridge initialization failed: {e}")
                self.use_mql5_bridge = False
        
        logger.info("TradingEngine initialized")

    def _ensure_dataframe(self, market_data) -> Optional[pd.DataFrame]:
        """
        Convert market data to pandas DataFrame format

        Args:
            market_data: Market data in various formats (DataFrame, dict, list)

        Returns:
            pandas DataFrame or None if conversion fails
        """
        try:
            if isinstance(market_data, pd.DataFrame):
                return market_data

            elif isinstance(market_data, dict):
                # Convert dict to DataFrame
                if all(key in market_data for key in ['Close', 'High', 'Low']):
                    # Handle dict with lists as values
                    if isinstance(market_data['Close'], list):
                        df = pd.DataFrame(market_data)

                        # Ensure required columns exist
                        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                        for col in required_cols:
                            if col not in df.columns:
                                if col == 'Open':
                                    df[col] = df['Close'].shift(1).fillna(df['Close'])
                                elif col == 'Volume':
                                    df[col] = 1000  # Default volume
                                else:
                                    df[col] = df['Close']

                        # Create datetime index if not present
                        if df.index.dtype != 'datetime64[ns]':
                            df.index = pd.date_range(start='2024-01-01', periods=len(df), freq='5min')

                        return df
                    else:
                        # Single row dict
                        df = pd.DataFrame([market_data])
                        return df
                else:
                    logger.warning("⚠️ Dict missing required price columns")
                    return None

            elif isinstance(market_data, list):
                # Convert list to DataFrame
                if len(market_data) > 0:
                    if isinstance(market_data[0], dict):
                        # List of dicts
                        df = pd.DataFrame(market_data)
                    else:
                        # List of values - assume Close prices
                        df = pd.DataFrame({
                            'Close': market_data,
                            'High': market_data,
                            'Low': market_data,
                            'Open': market_data,
                            'Volume': [1000] * len(market_data)
                        })

                    # Create datetime index
                    if df.index.dtype != 'datetime64[ns]':
                        df.index = pd.date_range(start='2024-01-01', periods=len(df), freq='5min')

                    return df
                else:
                    logger.warning("⚠️ Empty list provided")
                    return None

            else:
                logger.warning(f"⚠️ Unsupported market data type: {type(market_data)}")
                return None

        except Exception as e:
            logger.error(f"❌ Error converting market data to DataFrame: {e}")
            return None

    def analyze_market_setup(self, market_data: pd.DataFrame) -> Dict[str, any]:
        """
        Analyze current market setup using SMC principles

        Args:
            market_data: DataFrame with OHLCV data

        Returns:
            Dictionary with market analysis
        """
        try:
            # Ensure we have a valid DataFrame
            if market_data is None or len(market_data) == 0:
                return {
                    'error': 'No market data available',
                    'current_price': 0.0,
                    'trend': 'UNKNOWN',
                    'order_blocks': [],
                    'liquidity_zones': [],
                    'setup_quality': 0
                }

            from .indicators import SMCIndicators

            smc = SMCIndicators()
            analysis = smc.analyze_market_structure(market_data)
            
            # Add setup quality scoring
            setup_score = self._calculate_setup_quality(analysis)
            analysis['setup_quality'] = setup_score
            
            logger.info(f"Market setup analyzed - Quality: {setup_score}/10")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing market setup: {str(e)}")
            return {
                'timestamp': datetime.now(),
                'current_price': 1987.0,
                'trend': 'NEUTRAL',
                'setup_quality': 0
            }
    
    def _calculate_setup_quality(self, analysis: Dict) -> int:
        """
        Calculate setup quality score (1-10)
        
        Args:
            analysis: Market structure analysis
            
        Returns:
            Quality score from 1-10
        """
        try:
            score = 5  # Base score
            
            # Trend alignment (+2 points)
            if analysis.get('trend') in ['BULLISH', 'BEARISH']:
                score += 2
            
            # Order blocks present (+1 point)
            if len(analysis.get('order_blocks', [])) > 0:
                score += 1
            
            # BOS confirmation (+2 points)
            if analysis.get('bos_analysis', {}).get('bos_detected', False):
                score += 2
            
            # Liquidity grabs (+1 point)
            if len(analysis.get('liquidity_grabs', [])) > 0:
                score += 1
            
            # RSI not oversold/overbought (-1 point if extreme)
            rsi = analysis.get('indicators', {}).get('rsi', 50)
            if 30 <= rsi <= 70:
                score += 1
            elif rsi < 20 or rsi > 80:
                score -= 1
            
            return max(1, min(10, score))
            
        except Exception as e:
            logger.error(f"Error calculating setup quality: {str(e)}")
            return 5
    
    def validate_smc_strategy_setup(self, analysis: Dict) -> Dict[str, any]:
        """
        Validate setup using exact SMC strategy steps from strategy.md:
        Step 1: Identify Liquidity
        Step 2: Liquidity Grab (Stop Hunt)
        Step 3: Structure Shift (BOS)
        Step 4: Retest Entry

        Args:
            analysis: Market structure analysis

        Returns:
            Validation results following SMC strategy
        """
        try:
            validation = {
                'valid': False,
                'reasons': [],
                'trade_direction': 'HOLD',
                'confidence': 0.0,
                'smc_steps_completed': []
            }

            # Step 1: Identify Liquidity (Session levels and previous highs/lows)
            session_levels = analysis.get('session_levels', {})
            if not session_levels:
                validation['reasons'].append("Step 1 FAILED: No session liquidity levels identified")
                return validation
            validation['smc_steps_completed'].append("Step 1: Liquidity identified")

            # Step 2: Liquidity Grab (Stop Hunt) - Check for liquidity grabs
            liquidity_grabs = analysis.get('liquidity_grabs', [])
            if len(liquidity_grabs) == 0:
                validation['reasons'].append("Step 2 FAILED: No liquidity grab detected")
                return validation

            # Check if liquidity grab is recent (within last few candles)
            recent_grab = any(grab for grab in liquidity_grabs[-2:])  # Last 2 grabs
            if not recent_grab:
                validation['reasons'].append("Step 2 FAILED: No recent liquidity grab")
                return validation
            validation['smc_steps_completed'].append("Step 2: Liquidity grab confirmed")

            # Step 3: Structure Shift (BOS) - Confirm Break of Structure
            bos = analysis.get('bos_analysis', {})
            if not bos.get('bos_detected', False):
                validation['reasons'].append("Step 3 FAILED: No Break of Structure confirmation")
                return validation

            bos_direction = bos.get('direction', 'NEUTRAL')
            if bos_direction == 'NEUTRAL':
                validation['reasons'].append("Step 3 FAILED: BOS direction unclear")
                return validation
            validation['smc_steps_completed'].append(f"Step 3: BOS confirmed ({bos_direction})")

            # Step 4: Retest Entry - Check for Order Block retest opportunity
            order_blocks = analysis.get('order_blocks', [])
            if len(order_blocks) == 0:
                validation['reasons'].append("Step 4 FAILED: No Order Blocks for retest entry")
                return validation

            # Find fresh order blocks that align with BOS direction
            valid_obs = []
            for ob in order_blocks:
                if ob.get('status') == 'fresh':
                    # Check if OB direction aligns with BOS
                    if ((bos_direction == 'BULLISH' and ob.get('type') == 'bullish') or
                        (bos_direction == 'BEARISH' and ob.get('type') == 'bearish')):
                        valid_obs.append(ob)

            if len(valid_obs) == 0:
                validation['reasons'].append("Step 4 FAILED: No valid Order Blocks aligned with BOS direction")
                return validation

            validation['smc_steps_completed'].append("Step 4: Order Block retest opportunity identified")

            # All SMC strategy steps completed successfully
            validation['valid'] = True
            validation['trade_direction'] = 'BUY' if bos_direction == 'BULLISH' else 'SELL'

            # Calculate confidence based on setup quality and step completion
            base_confidence = 0.6  # Base for completing all steps
            setup_quality = analysis.get('setup_quality', 5)
            quality_bonus = (setup_quality - 5) * 0.05  # +5% per quality point above 5

            # Bonus for multiple liquidity grabs
            if len(liquidity_grabs) > 1:
                quality_bonus += 0.1

            # Bonus for strong BOS
            bos_strength = bos.get('strength', 5)
            if bos_strength >= 7:
                quality_bonus += 0.1

            validation['confidence'] = min(0.95, base_confidence + quality_bonus)
            validation['reasons'].append(f"All 4 SMC strategy steps completed successfully")
            validation['selected_order_block'] = valid_obs[0]  # Use strongest OB

            logger.info(f"SMC Strategy validated: {validation['trade_direction']} with {validation['confidence']:.2f} confidence")
            return validation

        except Exception as e:
            logger.error(f"Error validating SMC strategy setup: {str(e)}")
            return {
                'valid': False,
                'reasons': [f"SMC validation error: {str(e)}"],
                'trade_direction': 'HOLD',
                'confidence': 0.0,
                'smc_steps_completed': []
            }

    def validate_trade_setup(self, analysis: Dict) -> Dict[str, any]:
        """
        Main validation function that uses SMC strategy validation

        Args:
            analysis: Market structure analysis

        Returns:
            Validation results
        """
        return self.validate_smc_strategy_setup(analysis)
    
    def calculate_position_size(self, account_balance: float, risk_percentage: float, 
                              entry_price: float, stop_loss: float) -> Dict[str, float]:
        """
        Calculate position size based on risk management rules
        
        Args:
            account_balance: Current account balance
            risk_percentage: Risk percentage (0.01 = 1%)
            entry_price: Planned entry price
            stop_loss: Stop loss price
            
        Returns:
            Position sizing information
        """
        try:
            # Calculate risk amount
            risk_amount = account_balance * min(risk_percentage, self.max_risk_per_trade)
            
            # Calculate pip value for XAUUSD (typically $1 per pip for 0.01 lot)
            pip_value = 1.0  # $1 per pip for 0.01 lot
            
            # Calculate stop loss distance in pips
            sl_distance_pips = abs(entry_price - stop_loss) * 100  # Convert to pips
            
            if sl_distance_pips == 0:
                return {'lot_size': 0.0, 'risk_amount': 0.0, 'pip_value': 0.0}
            
            # Calculate lot size
            lot_size = risk_amount / (sl_distance_pips * pip_value)
            
            # Apply minimum and maximum lot size limits
            lot_size = max(0.01, min(1.0, lot_size))  # Between 0.01 and 1.0 lots
            
            return {
                'lot_size': round(lot_size, 2),
                'risk_amount': risk_amount,
                'pip_value': pip_value,
                'sl_distance_pips': sl_distance_pips
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return {'lot_size': 0.01, 'risk_amount': 0.0, 'pip_value': 1.0}
    
    def generate_trade_signal(self, market_data, account_info: Dict) -> Dict[str, any]:
        """
        Generate complete trade signal with all parameters

        Args:
            market_data: Market price data (DataFrame, dict, or list)
            account_info: Account information

        Returns:
            Complete trade signal
        """
        try:
            # Convert market_data to DataFrame if needed
            df = self._ensure_dataframe(market_data)

            if df is None or len(df) == 0:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reasons': ['No valid market data'],
                    'analysis': {'error': 'Invalid market data format'}
                }

            # Analyze market setup
            analysis = self.analyze_market_setup(df)
            
            # Validate setup
            validation = self.validate_trade_setup(analysis)
            
            if not validation['valid']:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reasons': validation['reasons'],
                    'analysis': analysis
                }
            
            # Calculate entry and exit levels using SMC strategy methodology
            current_price = analysis['current_price']
            selected_ob = validation.get('selected_order_block', {})
            session_levels = analysis.get('session_levels', {})

            if validation['trade_direction'] == 'BUY':
                # SMC BUY Setup: Enter on retest of bullish Order Block
                entry_price = selected_ob.get('top', current_price)  # Enter at OB top

                # Stop Loss: 3-7 pips below Order Block (as per strategy)
                pip_value = 0.01  # For XAUUSD
                stop_loss_pips = 5  # 5 pips below OB
                stop_loss = selected_ob.get('bottom', current_price - 0.50) - (stop_loss_pips * pip_value)

                # Take Profit: Target VWAP or 1:2 risk-reward ratio
                risk_distance = abs(entry_price - stop_loss)
                vwap = analysis.get('indicators', {}).get('vwap', current_price + (risk_distance * 2))

                # Use VWAP if it provides good R:R, otherwise use 1:2 ratio
                tp_vwap = vwap
                tp_ratio = entry_price + (risk_distance * 2.0)  # 1:2 risk-reward

                # Choose the closer target for conservative approach
                take_profit = min(tp_vwap, tp_ratio) if tp_vwap > entry_price else tp_ratio

            else:  # SELL
                # SMC SELL Setup: Enter on retest of bearish Order Block
                entry_price = selected_ob.get('bottom', current_price)  # Enter at OB bottom

                # Stop Loss: 3-7 pips above Order Block
                stop_loss_pips = 5  # 5 pips above OB
                stop_loss = selected_ob.get('top', current_price + 0.50) + (stop_loss_pips * pip_value)

                # Take Profit: Target VWAP or 1:2 risk-reward ratio
                risk_distance = abs(entry_price - stop_loss)
                vwap = analysis.get('indicators', {}).get('vwap', current_price - (risk_distance * 2))

                # Use VWAP if it provides good R:R, otherwise use 1:2 ratio
                tp_vwap = vwap
                tp_ratio = entry_price - (risk_distance * 2.0)  # 1:2 risk-reward

                # Choose the closer target for conservative approach
                take_profit = max(tp_vwap, tp_ratio) if tp_vwap < entry_price else tp_ratio
            
            # Calculate position size
            account_balance = account_info.get('balance', 100000)
            risk_percentage = 0.01  # 1% risk
            
            position_info = self.calculate_position_size(
                account_balance, risk_percentage, entry_price, stop_loss
            )
            
            # Calculate risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            signal = {
                'signal': validation['trade_direction'],
                'confidence': validation['confidence'],
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'risk_reward_ratio': round(risk_reward_ratio, 2),
                'lot_size': position_info['lot_size'],
                'risk_amount': position_info['risk_amount'],
                'setup_quality': analysis['setup_quality'],
                'reasons': validation['reasons'],
                'analysis': analysis,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Trade signal generated: {signal['signal']} at {signal['entry_price']}")
            return signal
            
        except Exception as e:
            logger.error(f"Error generating trade signal: {str(e)}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reasons': [f"Signal generation error: {str(e)}"],
                'timestamp': datetime.now()
            }

    def execute_trade_via_mql5(self, signal: Dict) -> Dict:
        """
        Execute trade via MQL5 Expert Advisor

        Args:
            signal: Trading signal from generate_trade_signal()

        Returns:
            dict: Execution results
        """
        if not self.use_mql5_bridge or not self.mql5_bridge:
            return {
                'success': False,
                'message': 'MQL5 Bridge not available',
                'method': 'direct_mt5_required'
            }

        try:
            # Extract signal data
            action = signal.get('signal', 'HOLD').upper()
            confidence = signal.get('confidence', 0.5)
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            take_profit = signal.get('take_profit', 0)
            analysis = signal.get('analysis', 'AI Trading Signal')

            # Send signal to MQL5 EA
            if action == 'BUY':
                success = self.mql5_bridge.send_buy_signal(
                    price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    analysis=analysis
                )
            elif action == 'SELL':
                success = self.mql5_bridge.send_sell_signal(
                    price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    analysis=analysis
                )
            elif action == 'CLOSE':
                success = self.mql5_bridge.send_close_signal(analysis=analysis)
            else:  # HOLD
                success = self.mql5_bridge.send_hold_signal(analysis=analysis)

            if not success:
                return {
                    'success': False,
                    'message': 'Failed to send signal to MQL5 EA',
                    'method': 'mql5_bridge'
                }

            # Wait for execution results
            logger.info(f"📤 Signal sent to MQL5 EA: {action}")
            results = self.mql5_bridge.wait_for_execution(timeout=30)

            if results:
                return {
                    'success': True,
                    'message': f'Trade executed via MQL5: {action}',
                    'method': 'mql5_bridge',
                    'execution_results': results,
                    'account_status': self.mql5_bridge.get_account_status()
                }
            else:
                return {
                    'success': False,
                    'message': 'MQL5 EA execution timeout',
                    'method': 'mql5_bridge'
                }

        except Exception as e:
            logger.error(f"❌ MQL5 execution error: {e}")
            return {
                'success': False,
                'message': f'MQL5 execution error: {str(e)}',
                'method': 'mql5_bridge'
            }

    def get_mql5_status(self) -> Dict:
        """Get MQL5 EA status and account information"""
        if not self.use_mql5_bridge or not self.mql5_bridge:
            return {
                'available': False,
                'message': 'MQL5 Bridge not initialized'
            }

        try:
            # Test connection
            connection_test = self.mql5_bridge.test_connection()
            account_status = self.mql5_bridge.get_account_status()

            return {
                'available': True,
                'ea_running': self.mql5_bridge.is_ea_running(),
                'connection_test': connection_test,
                'account_status': account_status,
                'data_path': str(self.mql5_bridge.data_path)
            }

        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }

# Test function
def test_trading_engine():
    """Test trading engine with sample data"""
    print("🔍 Testing Trading Engine...")
    
    # Create sample market data
    dates = pd.date_range(start='2025-01-01', periods=50, freq='5T')
    np.random.seed(42)
    
    data = []
    base_price = 1987.0
    for i, date in enumerate(dates):
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
    
    # Test trading engine
    engine = TradingEngine()
    
    # Sample account info
    account_info = {
        'balance': 100000,
        'equity': 100000,
        'currency': 'USD'
    }
    
    # Generate trade signal
    signal = engine.generate_trade_signal(df, account_info)
    
    print("✅ Trading Engine Test Results:")
    print(f"   Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']:.2f}")
    print(f"   Entry Price: ${signal.get('entry_price', 0):.2f}")
    print(f"   Stop Loss: ${signal.get('stop_loss', 0):.2f}")
    print(f"   Take Profit: ${signal.get('take_profit', 0):.2f}")
    print(f"   Risk-Reward: 1:{signal.get('risk_reward_ratio', 0):.1f}")
    print(f"   Lot Size: {signal.get('lot_size', 0):.2f}")
    print(f"   Setup Quality: {signal.get('setup_quality', 0)}/10")
    
    return True

if __name__ == "__main__":
    test_trading_engine()
