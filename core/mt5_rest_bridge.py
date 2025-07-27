#!/usr/bin/env python3
"""
Gold Digger AI Bot - MT5 REST API Bridge
Solution for MT5 integration on macOS via Windows VM/machine
Based on the forum solution by David _Detnator_
"""

import requests
import json
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MT5RestBridge:
    """
    REST API bridge to connect macOS app with Windows MT5 instance
    This solves the MT5 macOS compatibility issue
    """
    
    def __init__(self, bridge_host="192.168.1.100", bridge_port=8080):
        """
        Initialize MT5 REST bridge
        
        Args:
            bridge_host: IP address of Windows machine running MT5 REST server
            bridge_port: Port of the REST API server
        """
        self.base_url = f"http://{bridge_host}:{bridge_port}"
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_connection(self):
        """Test connection to MT5 REST bridge"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return {"success": True, "message": "MT5 REST bridge connected"}
            else:
                return {"success": False, "message": f"Bridge responded with {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}
    
    def initialize_mt5(self):
        """Initialize MT5 connection via REST API"""
        try:
            response = self.session.post(f"{self.base_url}/mt5/initialize")
            if response.status_code == 200:
                data = response.json()
                return {"success": data.get("success", False), "message": data.get("message", "")}
            else:
                return {"success": False, "message": f"Failed to initialize MT5: {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_account_info(self):
        """Get MT5 account information via REST API"""
        try:
            response = self.session.get(f"{self.base_url}/mt5/account")
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": "Failed to get account info"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_market_data(self, symbol="XAUUSD", timeframe="M5", count=100):
        """Get market data via REST API"""
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe,
                "count": count
            }
            response = self.session.get(f"{self.base_url}/mt5/rates", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Convert to DataFrame
                    rates_data = data.get("data", [])
                    if rates_data:
                        df = pd.DataFrame(rates_data)
                        df['datetime'] = pd.to_datetime(df['time'], unit='s')
                        return df
                    else:
                        return pd.DataFrame()
                else:
                    logger.error(f"MT5 REST API error: {data.get('message')}")
                    return pd.DataFrame()
            else:
                logger.error(f"REST API request failed: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return pd.DataFrame()
    
    def place_order(self, symbol, order_type, volume, price=None, sl=None, tp=None):
        """Place order via REST API"""
        try:
            order_data = {
                "symbol": symbol,
                "order_type": order_type,
                "volume": volume,
                "price": price,
                "sl": sl,
                "tp": tp
            }
            
            response = self.session.post(f"{self.base_url}/mt5/order", json=order_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Order failed: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_positions(self):
        """Get open positions via REST API"""
        try:
            response = self.session.get(f"{self.base_url}/mt5/positions")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("positions", [])
                else:
                    return []
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def close_position(self, ticket):
        """Close position via REST API"""
        try:
            response = self.session.post(f"{self.base_url}/mt5/close/{ticket}")
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Close failed: {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

# Configuration for different setups
MT5_BRIDGE_CONFIGS = {
    "local_vm": {
        "host": "127.0.0.1",  # VMware/Parallels local VM
        "port": 8080,
        "description": "Local Windows VM on same Mac"
    },
    "intel_mac": {
        "host": "192.168.1.100",  # Replace with actual IP
        "port": 8080,
        "description": "Separate Intel Mac running Windows"
    },
    "windows_pc": {
        "host": "192.168.1.101",  # Replace with actual IP
        "port": 8080,
        "description": "Dedicated Windows PC with MT5"
    }
}

def create_mt5_bridge(config_name="local_vm"):
    """Create MT5 bridge with predefined configuration"""
    config = MT5_BRIDGE_CONFIGS.get(config_name)
    if config:
        return MT5RestBridge(config["host"], config["port"])
    else:
        raise ValueError(f"Unknown config: {config_name}")

# Test function
if __name__ == "__main__":
    print("🔍 Testing MT5 REST Bridge...")
    
    # Test with local VM configuration
    bridge = create_mt5_bridge("local_vm")
    
    # Test connection
    result = bridge.test_connection()
    print(f"Connection test: {result}")
    
    if result["success"]:
        # Test MT5 initialization
        init_result = bridge.initialize_mt5()
        print(f"MT5 initialization: {init_result}")
        
        if init_result["success"]:
            # Test account info
            account = bridge.get_account_info()
            print(f"Account info: {account}")
            
            # Test market data
            data = bridge.get_market_data("XAUUSD", "M5", 10)
            print(f"Market data: {len(data)} candles retrieved")
    
    print("🎯 To use this bridge:")
    print("1. Set up Windows VM with MT5 and REST API server")
    print("2. Update the host IP in MT5_BRIDGE_CONFIGS")
    print("3. Your macOS app will connect via REST API")
    print("4. Full MT5 functionality on macOS! 🚀")
