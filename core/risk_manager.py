"""
Gold Digger AI Bot - Risk Management
Advanced risk management and position sizing for safe trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManager:
    """
    Advanced risk management system for trading operations
    Handles position sizing, drawdown protection, and risk controls
    """
    
    def __init__(self):
        """Initialize risk manager with default settings"""
        # Risk parameters from environment or defaults
        self.max_risk_per_trade = float(os.getenv('RISK_PER_TRADE', '0.01'))  # 1%
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '500.0'))
        self.max_positions = int(os.getenv('MAX_POSITIONS', '3'))
        self.max_drawdown = 0.10  # 10% maximum drawdown
        
        # Trading session limits (per strategy.md)
        self.max_trades_per_day = 4  # Strategy.md: Maximum 3-4 setups per day
        self.max_trades_per_hour = 2
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.trade_count_today = 0
        self.current_drawdown = 0.0
        
        logger.info("RiskManager initialized")
    
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                              stop_loss: float, risk_percentage: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            account_balance: Current account balance
            entry_price: Planned entry price
            stop_loss: Stop loss price
            risk_percentage: Custom risk percentage (optional)
            
        Returns:
            Position sizing information
        """
        try:
            # Use custom risk or default
            risk_pct = risk_percentage or self.max_risk_per_trade
            
            # Calculate risk amount
            risk_amount = account_balance * risk_pct
            
            # Calculate stop loss distance in price
            sl_distance = abs(entry_price - stop_loss)
            
            if sl_distance == 0:
                logger.warning("Stop loss distance is zero - cannot calculate position size")
                return self._get_zero_position()
            
            # For XAUUSD: 1 pip = 0.01, lot size affects pip value
            # Standard lot (1.0) = $10 per pip, Mini lot (0.1) = $1 per pip, Micro lot (0.01) = $0.10 per pip
            pip_size = 0.01
            pips_at_risk = sl_distance / pip_size
            
            # Calculate lot size (assuming $1 per pip for 0.1 lot)
            pip_value_per_mini_lot = 1.0
            required_lots = risk_amount / (pips_at_risk * pip_value_per_mini_lot)
            
            # Apply lot size limits
            min_lot = 0.01
            max_lot = 1.0  # Conservative maximum
            
            lot_size = max(min_lot, min(max_lot, required_lots))
            
            # Calculate actual risk with final lot size
            actual_pip_value = lot_size * 10  # $10 per pip for 1.0 lot
            actual_risk = pips_at_risk * (actual_pip_value / 10)  # Adjust for lot size
            
            result = {
                'lot_size': round(lot_size, 2),
                'risk_amount': round(actual_risk, 2),
                'pip_value': round(actual_pip_value / 10, 2),
                'pips_at_risk': round(pips_at_risk, 1),
                'risk_percentage': round((actual_risk / account_balance) * 100, 2)
            }
            
            logger.info(f"Position size calculated: {result['lot_size']} lots, ${result['risk_amount']} risk")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return self._get_zero_position()
    
    def _get_zero_position(self) -> Dict[str, float]:
        """Return zero position sizing"""
        return {
            'lot_size': 0.0,
            'risk_amount': 0.0,
            'pip_value': 0.0,
            'pips_at_risk': 0.0,
            'risk_percentage': 0.0
        }
    
    def validate_trade_risk(self, trade_signal: Dict, account_info: Dict) -> Dict[str, any]:
        """
        Validate if trade meets risk management criteria
        
        Args:
            trade_signal: Trade signal with entry, SL, TP
            account_info: Current account information
            
        Returns:
            Risk validation results
        """
        try:
            validation = {
                'approved': False,
                'reasons': [],
                'risk_score': 0,
                'adjusted_lot_size': 0.0
            }
            
            account_balance = account_info.get('balance', 100000)
            account_equity = account_info.get('equity', account_balance)
            
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                validation['reasons'].append(f"Daily loss limit reached: ${abs(self.daily_pnl):.2f}")
                return validation
            
            # Check maximum drawdown
            current_drawdown = (account_balance - account_equity) / account_balance
            if current_drawdown >= self.max_drawdown:
                validation['reasons'].append(f"Maximum drawdown exceeded: {current_drawdown:.1%}")
                return validation
            
            # Check trade count limits
            if self.trade_count_today >= self.max_trades_per_day:
                validation['reasons'].append(f"Daily trade limit reached: {self.trade_count_today}")
                return validation
            
            # Validate trade signal components
            entry_price = trade_signal.get('entry_price', 0)
            stop_loss = trade_signal.get('stop_loss', 0)
            take_profit = trade_signal.get('take_profit', 0)
            
            if not all([entry_price, stop_loss, take_profit]):
                validation['reasons'].append("Missing trade signal components")
                return validation
            
            # Calculate risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            
            if risk == 0:
                validation['reasons'].append("Invalid stop loss - no risk defined")
                return validation
            
            risk_reward_ratio = reward / risk
            
            if risk_reward_ratio < 1.5:
                validation['reasons'].append(f"Risk-reward ratio too low: 1:{risk_reward_ratio:.1f}")
                return validation
            
            # Calculate position size
            position_info = self.calculate_position_size(account_balance, entry_price, stop_loss)
            
            if position_info['lot_size'] == 0:
                validation['reasons'].append("Cannot calculate valid position size")
                return validation
            
            # Check if risk amount is acceptable
            if position_info['risk_amount'] > account_balance * self.max_risk_per_trade:
                validation['reasons'].append(f"Risk amount too high: ${position_info['risk_amount']:.2f}")
                return validation
            
            # Calculate risk score (1-10, higher is better)
            risk_score = self._calculate_risk_score(trade_signal, position_info, account_info)
            
            # All checks passed
            validation['approved'] = True
            validation['risk_score'] = risk_score
            validation['adjusted_lot_size'] = position_info['lot_size']
            validation['position_info'] = position_info
            validation['risk_reward_ratio'] = risk_reward_ratio
            validation['reasons'].append("All risk criteria met")
            
            logger.info(f"Trade risk validated: Score {risk_score}/10, Lot size {position_info['lot_size']}")
            return validation
            
        except Exception as e:
            logger.error(f"Error validating trade risk: {str(e)}")
            return {
                'approved': False,
                'reasons': [f"Risk validation error: {str(e)}"],
                'risk_score': 0,
                'adjusted_lot_size': 0.0
            }
    
    def _calculate_risk_score(self, trade_signal: Dict, position_info: Dict, account_info: Dict) -> int:
        """
        Calculate risk score for the trade (1-10)
        
        Args:
            trade_signal: Trade signal information
            position_info: Position sizing information
            account_info: Account information
            
        Returns:
            Risk score from 1-10 (higher is better)
        """
        try:
            score = 5  # Base score
            
            # Risk-reward ratio bonus
            rr_ratio = trade_signal.get('risk_reward_ratio', 1.0)
            if rr_ratio >= 3.0:
                score += 2
            elif rr_ratio >= 2.0:
                score += 1
            
            # Setup quality bonus
            setup_quality = trade_signal.get('setup_quality', 5)
            if setup_quality >= 8:
                score += 2
            elif setup_quality >= 6:
                score += 1
            
            # Confidence bonus
            confidence = trade_signal.get('confidence', 0.5)
            if confidence >= 0.8:
                score += 1
            
            # Risk percentage penalty
            risk_pct = position_info.get('risk_percentage', 1.0)
            if risk_pct <= 0.5:
                score += 1
            elif risk_pct >= 2.0:
                score -= 1
            
            # Account health bonus
            account_balance = account_info.get('balance', 100000)
            account_equity = account_info.get('equity', account_balance)
            equity_ratio = account_equity / account_balance
            
            if equity_ratio >= 0.98:
                score += 1
            elif equity_ratio <= 0.90:
                score -= 2
            
            return max(1, min(10, score))
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 5
    
    def update_daily_pnl(self, pnl_change: float):
        """
        Update daily P&L tracking
        
        Args:
            pnl_change: P&L change from completed trade
        """
        try:
            self.daily_pnl += pnl_change
            logger.info(f"Daily P&L updated: ${self.daily_pnl:.2f}")
            
            # Check if daily loss limit is approaching
            if self.daily_pnl <= -self.max_daily_loss * 0.8:
                logger.warning(f"Approaching daily loss limit: ${abs(self.daily_pnl):.2f}")
                
        except Exception as e:
            logger.error(f"Error updating daily P&L: {str(e)}")
    
    def increment_trade_count(self):
        """Increment daily trade count"""
        self.trade_count_today += 1
        logger.info(f"Trade count updated: {self.trade_count_today}/{self.max_trades_per_day}")
    
    def reset_daily_counters(self):
        """Reset daily counters (call at start of new trading day)"""
        self.daily_pnl = 0.0
        self.trade_count_today = 0
        logger.info("Daily risk counters reset")
    
    def get_risk_status(self, account_info: Dict) -> Dict[str, any]:
        """
        Get current risk status summary
        
        Args:
            account_info: Current account information
            
        Returns:
            Risk status summary
        """
        try:
            account_balance = account_info.get('balance', 100000)
            account_equity = account_info.get('equity', account_balance)
            
            # Calculate current drawdown
            drawdown = max(0, (account_balance - account_equity) / account_balance)
            
            # Calculate remaining daily risk
            remaining_daily_risk = max(0, self.max_daily_loss + self.daily_pnl)
            
            # Calculate risk utilization
            risk_utilization = abs(self.daily_pnl) / self.max_daily_loss if self.max_daily_loss > 0 else 0
            
            status = {
                'daily_pnl': round(self.daily_pnl, 2),
                'remaining_daily_risk': round(remaining_daily_risk, 2),
                'risk_utilization': round(risk_utilization * 100, 1),
                'trade_count': self.trade_count_today,
                'remaining_trades': max(0, self.max_trades_per_day - self.trade_count_today),
                'current_drawdown': round(drawdown * 100, 2),
                'max_drawdown_limit': round(self.max_drawdown * 100, 1),
                'account_health': 'GOOD' if drawdown < 0.05 else 'WARNING' if drawdown < 0.08 else 'CRITICAL',
                'trading_allowed': self._is_trading_allowed(account_info)
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting risk status: {str(e)}")
            return {
                'daily_pnl': 0.0,
                'remaining_daily_risk': self.max_daily_loss,
                'risk_utilization': 0.0,
                'trade_count': 0,
                'remaining_trades': self.max_trades_per_day,
                'current_drawdown': 0.0,
                'account_health': 'UNKNOWN',
                'trading_allowed': False
            }
    
    def _is_trading_allowed(self, account_info: Dict) -> bool:
        """
        Check if trading is currently allowed based on risk parameters
        
        Args:
            account_info: Account information
            
        Returns:
            True if trading is allowed
        """
        try:
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                return False
            
            # Check trade count limit
            if self.trade_count_today >= self.max_trades_per_day:
                return False
            
            # Check drawdown limit
            account_balance = account_info.get('balance', 100000)
            account_equity = account_info.get('equity', account_balance)
            drawdown = (account_balance - account_equity) / account_balance
            
            if drawdown >= self.max_drawdown:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trading allowance: {str(e)}")
            return False

# Test function
def test_risk_manager():
    """Test risk manager functionality"""
    print("🔍 Testing Risk Manager...")
    
    # Create risk manager
    risk_manager = RiskManager()
    
    # Sample account info
    account_info = {
        'balance': 100000,
        'equity': 99500,
        'currency': 'USD'
    }
    
    # Sample trade signal
    trade_signal = {
        'signal': 'BUY',
        'entry_price': 1987.50,
        'stop_loss': 1985.00,
        'take_profit': 1992.50,
        'confidence': 0.85,
        'setup_quality': 8,
        'risk_reward_ratio': 2.0
    }
    
    # Test position sizing
    position_info = risk_manager.calculate_position_size(
        account_info['balance'], 
        trade_signal['entry_price'], 
        trade_signal['stop_loss']
    )
    
    # Test risk validation
    validation = risk_manager.validate_trade_risk(trade_signal, account_info)
    
    # Test risk status
    risk_status = risk_manager.get_risk_status(account_info)
    
    print("✅ Risk Manager Test Results:")
    print(f"   Position Size: {position_info['lot_size']} lots")
    print(f"   Risk Amount: ${position_info['risk_amount']:.2f}")
    print(f"   Risk Percentage: {position_info['risk_percentage']:.2f}%")
    print(f"   Trade Approved: {validation['approved']}")
    print(f"   Risk Score: {validation['risk_score']}/10")
    print(f"   Account Health: {risk_status['account_health']}")
    print(f"   Trading Allowed: {risk_status['trading_allowed']}")
    
    return True

if __name__ == "__main__":
    test_risk_manager()
