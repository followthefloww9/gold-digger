#!/usr/bin/env python3
"""
Gold Digger AI Bot - cTrader API Integration
Native macOS solution using IC Markets cTrader API
No Windows VM required - works on any platform
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import hashlib
import hmac
import base64
import logging

logger = logging.getLogger(__name__)

class CTraderAPI:
    """
    Native macOS solution using cTrader Open API
    IC Markets supports cTrader which has REST API
    Works on macOS without Windows VM
    """
    
    def __init__(self, client_id, client_secret, access_token, environment="demo"):
        """
        Initialize cTrader API connection
        
        Args:
            client_id: cTrader API client ID
            client_secret: cTrader API client secret
            access_token: OAuth access token
            environment: "demo" or "live"
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.environment = environment
        
        # API endpoints
        if environment == "demo":
            self.base_url = "https://demo-api.ctrader.com"
        else:
            self.base_url = "https://api.ctrader.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })
        
    def test_connection(self):
        """Test connection to cTrader API"""
        try:
            response = self.session.get(f"{self.base_url}/v1/accounts")
            
            if response.status_code == 200:
                accounts = response.json()
                return {
                    "success": True,
                    "message": "Connected to cTrader API",
                    "accounts": len(accounts.get('data', []))
                }
            else:
                return {
                    "success": False,
                    "message": f"API responded with {response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}
    
    def get_accounts(self):
        """Get trading accounts"""
        try:
            response = self.session.get(f"{self.base_url}/v1/accounts")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Failed to get accounts: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_account_info(self, account_id):
        """Get account information"""
        try:
            response = self.session.get(f"{self.base_url}/v1/accounts/{account_id}")
            
            if response.status_code == 200:
                account_data = response.json()
                return {
                    "success": True,
                    "account": {
                        "id": account_data.get("accountId"),
                        "login": account_data.get("login"),
                        "server": account_data.get("brokerName"),
                        "balance": account_data.get("balance", 0) / 100,  # Convert from cents
                        "equity": account_data.get("equity", 0) / 100,
                        "currency": account_data.get("depositCurrency"),
                        "leverage": account_data.get("leverage"),
                        "margin_level": account_data.get("marginLevel", 0) / 100
                    }
                }
            else:
                return {"success": False, "message": f"Failed to get account info: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_symbols(self, account_id):
        """Get available trading symbols"""
        try:
            response = self.session.get(f"{self.base_url}/v1/accounts/{account_id}/symbols")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Failed to get symbols: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_market_data(self, account_id, symbol_id, timeframe="M5", count=100):
        """Get historical market data"""
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=count * 5 / 60)  # Approximate for M5
            
            params = {
                'symbolId': symbol_id,
                'periodicity': timeframe,
                'fromTimestamp': int(start_time.timestamp() * 1000),
                'toTimestamp': int(end_time.timestamp() * 1000),
                'count': count
            }
            
            response = self.session.get(
                f"{self.base_url}/v1/accounts/{account_id}/ohlc",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert to DataFrame
                if 'data' in data and data['data']:
                    candles = data['data']
                    df = pd.DataFrame([
                        {
                            'datetime': pd.to_datetime(candle['timestamp'], unit='ms'),
                            'open': candle['open'] / 100000,  # Convert from points
                            'high': candle['high'] / 100000,
                            'low': candle['low'] / 100000,
                            'close': candle['close'] / 100000,
                            'volume': candle.get('volume', 0)
                        }
                        for candle in candles
                    ])
                    return df
                else:
                    return pd.DataFrame()
            else:
                logger.error(f"Failed to get market data: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return pd.DataFrame()
    
    def get_current_price(self, account_id, symbol_id):
        """Get current bid/ask prices"""
        try:
            response = self.session.get(f"{self.base_url}/v1/accounts/{account_id}/symbols/{symbol_id}/currentprice")
            
            if response.status_code == 200:
                price_data = response.json()
                return {
                    "success": True,
                    "bid": price_data.get("bid", 0) / 100000,
                    "ask": price_data.get("ask", 0) / 100000,
                    "timestamp": price_data.get("timestamp")
                }
            else:
                return {"success": False, "message": f"Failed to get price: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def place_order(self, account_id, symbol_id, side, volume, order_type="MARKET", price=None, stop_loss=None, take_profit=None):
        """Place trading order"""
        try:
            order_data = {
                "accountId": account_id,
                "symbolId": symbol_id,
                "orderType": order_type.upper(),
                "tradeSide": side.upper(),
                "volume": int(volume * 100),  # Convert to lots in cents
                "comment": "Gold Digger AI Bot"
            }
            
            if price and order_type != "MARKET":
                order_data["limitPrice"] = int(price * 100000)  # Convert to points
            
            if stop_loss:
                order_data["stopLoss"] = int(stop_loss * 100000)
            
            if take_profit:
                order_data["takeProfit"] = int(take_profit * 100000)
            
            response = self.session.post(
                f"{self.base_url}/v1/accounts/{account_id}/orders",
                json=order_data
            )
            
            if response.status_code == 200:
                order_result = response.json()
                return {
                    "success": True,
                    "message": "Order placed successfully",
                    "order_id": order_result.get("orderId"),
                    "position_id": order_result.get("positionId")
                }
            else:
                return {"success": False, "message": f"Order failed: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Order error: {str(e)}"}
    
    def get_positions(self, account_id):
        """Get open positions"""
        try:
            response = self.session.get(f"{self.base_url}/v1/accounts/{account_id}/positions")
            
            if response.status_code == 200:
                positions_data = response.json()
                
                positions = []
                for pos in positions_data.get('data', []):
                    positions.append({
                        "id": pos.get("positionId"),
                        "symbol": pos.get("symbolName"),
                        "side": pos.get("tradeSide"),
                        "volume": pos.get("volume", 0) / 100,
                        "entry_price": pos.get("entryPrice", 0) / 100000,
                        "current_price": pos.get("currentPrice", 0) / 100000,
                        "profit": pos.get("profit", 0) / 100,
                        "swap": pos.get("swap", 0) / 100,
                        "commission": pos.get("commission", 0) / 100
                    })
                
                return positions
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def close_position(self, account_id, position_id, volume=None):
        """Close position"""
        try:
            close_data = {
                "accountId": account_id,
                "positionId": position_id
            }
            
            if volume:
                close_data["volume"] = int(volume * 100)
            
            response = self.session.delete(
                f"{self.base_url}/v1/accounts/{account_id}/positions/{position_id}",
                json=close_data
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Position closed successfully"}
            else:
                return {"success": False, "message": f"Close failed: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Close error: {str(e)}"}

# Configuration for cTrader API
CTRADER_CONFIG = {
    "demo": {
        "auth_url": "https://demo-openapi.ctrader.com",
        "api_url": "https://demo-api.ctrader.com"
    },
    "live": {
        "auth_url": "https://openapi.ctrader.com", 
        "api_url": "https://api.ctrader.com"
    }
}

def create_ctrader_connection(client_id, client_secret, access_token, environment="demo"):
    """Create cTrader API connection"""
    return CTraderAPI(client_id, client_secret, access_token, environment)

# Test function
if __name__ == "__main__":
    print("🔍 Testing cTrader API (Native macOS Solution)...")
    print("💡 This requires cTrader API credentials from IC Markets")
    print("📞 Contact IC Markets to get cTrader API access")
    print("🚀 Once configured, this works natively on macOS!")
    print("")
    print("📋 Setup Steps:")
    print("1. Open IC Markets cTrader account")
    print("2. Register for cTrader Open API access")
    print("3. Get client_id, client_secret, and access_token")
    print("4. Update the credentials in your bot configuration")
    print("5. Enjoy native macOS trading! 🎉")
