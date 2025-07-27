"""
Gold Digger AI Bot - Position Sizing Calculator
Calculates optimal position sizes for gold trading based on risk management
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class PositionSize:
    """Position size calculation result"""
    lot_size: float  # MT5 lot size (e.g., 0.01 = 1 ounce)
    ounces: float    # Actual ounces of gold
    risk_amount: float  # Dollar amount at risk
    pip_value: float    # Value per pip movement
    stop_loss_distance: float  # Distance to stop loss in pips
    position_value: float  # Total position value in USD

class GoldPositionSizer:
    """
    Position sizing calculator for gold (XAUUSD) trading
    
    Based on MT5 gold contract specifications:
    - 1.0 lot = 100 ounces of gold
    - 0.01 lot = 1 ounce of gold (minimum)
    - 1 pip = $0.10 per 0.01 lot (1 ounce)
    - 1 pip = $10 per 1.0 lot (100 ounces)
    """
    
    def __init__(self):
        # Gold contract specifications (standard for most brokers)
        self.contract_size = 100  # ounces per 1.0 lot
        self.min_lot_size = 0.01  # minimum tradeable size
        self.max_lot_size = 50.0  # maximum lot size (varies by broker)
        self.lot_step = 0.01      # minimum increment
        self.pip_value_per_lot = 10.0  # $10 per pip for 1.0 lot
        
        logger.info("GoldPositionSizer initialized with standard MT5 specifications")
    
    def calculate_position_size(
        self,
        account_balance: float,
        risk_percentage: float,
        entry_price: float,
        stop_loss_price: float,
        max_risk_amount: Optional[float] = None
    ) -> PositionSize:
        """
        Calculate optimal position size for gold trade
        
        Args:
            account_balance: Account balance in USD
            risk_percentage: Risk as percentage (e.g., 1.0 for 1%)
            entry_price: Entry price for gold
            stop_loss_price: Stop loss price
            max_risk_amount: Maximum dollar amount to risk (optional)
            
        Returns:
            PositionSize object with calculated values
        """
        try:
            # Calculate risk amount
            risk_amount = account_balance * (risk_percentage / 100)
            
            # Apply maximum risk limit if specified
            if max_risk_amount and risk_amount > max_risk_amount:
                risk_amount = max_risk_amount
                logger.info(f"Risk amount capped at ${max_risk_amount:.2f}")
            
            # Calculate stop loss distance in dollars
            stop_loss_distance_usd = abs(entry_price - stop_loss_price)
            
            # Convert to pips (gold: 1 pip = $0.10 price movement)
            stop_loss_distance_pips = stop_loss_distance_usd * 10
            
            # Calculate ounces to trade
            # Formula: Risk Amount / Stop Loss Distance = Ounces
            ounces = risk_amount / stop_loss_distance_usd
            
            # Convert to MT5 lot size
            lot_size = ounces / self.contract_size
            
            # Round to valid lot step
            lot_size = round(lot_size / self.lot_step) * self.lot_step
            
            # Apply min/max limits
            lot_size = max(self.min_lot_size, min(lot_size, self.max_lot_size))
            
            # Recalculate actual values based on rounded lot size
            actual_ounces = lot_size * self.contract_size
            pip_value = lot_size * self.pip_value_per_lot
            position_value = actual_ounces * entry_price
            actual_risk = actual_ounces * stop_loss_distance_usd
            
            result = PositionSize(
                lot_size=lot_size,
                ounces=actual_ounces,
                risk_amount=actual_risk,
                pip_value=pip_value,
                stop_loss_distance=stop_loss_distance_pips,
                position_value=position_value
            )
            
            logger.info(f"Position calculated: {lot_size} lots ({actual_ounces} oz) risking ${actual_risk:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            # Return minimum position as fallback
            return PositionSize(
                lot_size=self.min_lot_size,
                ounces=1.0,
                risk_amount=0.0,
                pip_value=1.0,
                stop_loss_distance=0.0,
                position_value=0.0
            )
    
    def calculate_pip_value(self, lot_size: float) -> float:
        """Calculate pip value for given lot size"""
        return lot_size * self.pip_value_per_lot
    
    def validate_lot_size(self, lot_size: float) -> float:
        """Validate and adjust lot size to broker specifications"""
        # Round to valid step
        adjusted = round(lot_size / self.lot_step) * self.lot_step
        
        # Apply limits
        adjusted = max(self.min_lot_size, min(adjusted, self.max_lot_size))
        
        return adjusted
    
    def get_position_info(self, lot_size: float, current_price: float) -> Dict:
        """Get detailed position information"""
        ounces = lot_size * self.contract_size
        pip_value = self.calculate_pip_value(lot_size)
        position_value = ounces * current_price
        
        return {
            'lot_size': lot_size,
            'ounces': ounces,
            'pip_value': pip_value,
            'position_value': position_value,
            'contract_size': self.contract_size,
            'min_lot': self.min_lot_size,
            'max_lot': self.max_lot_size
        }

def calculate_risk_reward_ratio(
    entry_price: float,
    stop_loss_price: float,
    take_profit_price: float
) -> float:
    """Calculate risk-reward ratio for a trade"""
    risk = abs(entry_price - stop_loss_price)
    reward = abs(take_profit_price - entry_price)
    
    if risk == 0:
        return 0.0
    
    return reward / risk

# Example usage and testing
if __name__ == "__main__":
    # Test the position sizer
    sizer = GoldPositionSizer()
    
    # Example calculation
    position = sizer.calculate_position_size(
        account_balance=100000,  # $100K account
        risk_percentage=1.0,     # Risk 1%
        entry_price=2680.00,     # Gold at $2680
        stop_loss_price=2670.00  # Stop loss at $2670
    )
    
    print(f"Position Size: {position.lot_size} lots")
    print(f"Ounces: {position.ounces}")
    print(f"Risk Amount: ${position.risk_amount:.2f}")
    print(f"Pip Value: ${position.pip_value:.2f}")
    print(f"Position Value: ${position.position_value:.2f}")
