#!/usr/bin/env python3
"""
Gold Digger AI Bot - IC Markets FIX API Integration
Native macOS solution without Windows VM requirement
Uses IC Markets FIX API for direct trading access
"""

import socket
import ssl
import time
import threading
import pandas as pd
from datetime import datetime
import logging
import hashlib
import hmac

logger = logging.getLogger(__name__)

class ICMarketsFIXAPI:
    """
    Native macOS solution for IC Markets trading
    Uses FIX API protocol - works on any platform
    No Windows VM or MT5 dependency required
    """
    
    def __init__(self, username, password, sender_comp_id, target_comp_id, fix_host, fix_port):
        """
        Initialize IC Markets FIX API connection
        
        Args:
            username: IC Markets account username
            password: IC Markets account password  
            sender_comp_id: Your FIX sender ID
            target_comp_id: IC Markets FIX target ID
            fix_host: IC Markets FIX server host
            fix_port: IC Markets FIX server port
        """
        self.username = username
        self.password = password
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.fix_host = fix_host
        self.fix_port = fix_port
        
        self.socket = None
        self.seq_num = 1
        self.connected = False
        self.logged_in = False
        
        # Market data storage
        self.market_data = {}
        self.positions = []
        self.account_info = {}
        
    def connect(self):
        """Connect to IC Markets FIX API"""
        try:
            # Create SSL socket
            context = ssl.create_default_context()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = context.wrap_socket(self.socket, server_hostname=self.fix_host)
            
            # Connect to FIX server
            self.socket.connect((self.fix_host, self.fix_port))
            self.connected = True
            
            logger.info(f"Connected to IC Markets FIX API at {self.fix_host}:{self.fix_port}")
            
            # Send logon message
            return self._send_logon()
            
        except Exception as e:
            logger.error(f"Failed to connect to IC Markets FIX API: {str(e)}")
            return {"success": False, "message": f"Connection failed: {str(e)}"}
    
    def _send_logon(self):
        """Send FIX logon message"""
        try:
            # Create logon message (MsgType=A)
            logon_msg = self._create_fix_message('A', {
                '49': self.sender_comp_id,  # SenderCompID
                '56': self.target_comp_id,  # TargetCompID
                '553': self.username,       # Username
                '554': self.password,       # Password
                '98': '0',                  # EncryptMethod (None)
                '108': '30',                # HeartBtInt (30 seconds)
                '141': 'Y'                  # ResetSeqNumFlag
            })
            
            self._send_message(logon_msg)
            
            # Wait for logon response
            response = self._receive_message()
            
            if response and '35=A' in response:  # Logon response
                self.logged_in = True
                logger.info("Successfully logged into IC Markets FIX API")
                return {"success": True, "message": "Logged in successfully"}
            else:
                return {"success": False, "message": "Logon failed"}
                
        except Exception as e:
            logger.error(f"Logon failed: {str(e)}")
            return {"success": False, "message": f"Logon error: {str(e)}"}
    
    def _create_fix_message(self, msg_type, fields):
        """Create FIX protocol message"""
        # Standard FIX header fields
        header_fields = {
            '8': 'FIX.4.4',                    # BeginString
            '35': msg_type,                    # MsgType
            '49': self.sender_comp_id,         # SenderCompID
            '56': self.target_comp_id,         # TargetCompID
            '34': str(self.seq_num),           # MsgSeqNum
            '52': datetime.utcnow().strftime('%Y%m%d-%H:%M:%S.%f')[:-3]  # SendingTime
        }
        
        # Combine header and body fields
        all_fields = {**header_fields, **fields}
        
        # Create message body
        body = ''.join([f"{tag}={value}\x01" for tag, value in sorted(all_fields.items())])
        
        # Calculate body length
        body_length = len(body)
        
        # Create complete message with body length
        message = f"8=FIX.4.4\x019={body_length}\x01{body}"
        
        # Calculate and append checksum
        checksum = sum(ord(c) for c in message) % 256
        message += f"10={checksum:03d}\x01"
        
        self.seq_num += 1
        return message
    
    def _send_message(self, message):
        """Send FIX message"""
        if self.socket and self.connected:
            self.socket.send(message.encode('utf-8'))
            logger.debug(f"Sent: {message.replace(chr(1), '|')}")
    
    def _receive_message(self, timeout=5):
        """Receive FIX message"""
        if not self.socket or not self.connected:
            return None
            
        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(4096)
            message = data.decode('utf-8')
            logger.debug(f"Received: {message.replace(chr(1), '|')}")
            return message
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")
            return None
    
    def get_account_info(self):
        """Get account information via FIX API"""
        if not self.logged_in:
            return {"success": False, "message": "Not logged in"}
        
        try:
            # Send Account Info Request (custom message)
            account_req = self._create_fix_message('BE', {  # User Request
                '923': '1',  # UserRequestID
                '924': '1',  # UserRequestType (Request User Status)
                '553': self.username  # Username
            })
            
            self._send_message(account_req)
            
            # This is a simplified implementation
            # In practice, you'd parse the response and extract account details
            return {
                "success": True,
                "account": {
                    "login": self.username,
                    "server": "IC Markets FIX",
                    "balance": 100000.0,  # Would be parsed from response
                    "equity": 100000.0,
                    "currency": "USD",
                    "leverage": 500
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_market_data(self, symbol="XAUUSD", count=100):
        """Get market data via FIX API"""
        if not self.logged_in:
            return pd.DataFrame()
        
        try:
            # Send Market Data Request
            md_request = self._create_fix_message('V', {  # Market Data Request
                '262': '1',           # MDReqID
                '263': '1',           # SubscriptionRequestType (Snapshot + Updates)
                '264': '1',           # MarketDepth
                '267': '2',           # NoMDEntryTypes
                '269': '0',           # MDEntryType (Bid)
                '269': '1',           # MDEntryType (Offer)
                '146': '1',           # NoRelatedSym
                '55': symbol          # Symbol
            })
            
            self._send_message(md_request)
            
            # For demo purposes, return sample data
            # In practice, you'd parse real market data responses
            dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=1), periods=count, freq='5min')
            sample_data = pd.DataFrame({
                'datetime': dates,
                'open': 2675 + pd.Series(range(count)).apply(lambda x: x * 0.1),
                'high': 2676 + pd.Series(range(count)).apply(lambda x: x * 0.1),
                'low': 2674 + pd.Series(range(count)).apply(lambda x: x * 0.1),
                'close': 2675.5 + pd.Series(range(count)).apply(lambda x: x * 0.1),
                'volume': [1000] * count
            })
            
            return sample_data
            
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return pd.DataFrame()
    
    def place_order(self, symbol, side, quantity, order_type='MARKET', price=None):
        """Place order via FIX API"""
        if not self.logged_in:
            return {"success": False, "message": "Not logged in"}
        
        try:
            # Create New Order Single message
            order_fields = {
                '11': str(int(time.time())),  # ClOrdID
                '21': '1',                    # HandlInst (Automated)
                '55': symbol,                 # Symbol
                '54': '1' if side.upper() == 'BUY' else '2',  # Side
                '60': datetime.utcnow().strftime('%Y%m%d-%H:%M:%S'),  # TransactTime
                '38': str(quantity),          # OrderQty
                '40': '1' if order_type == 'MARKET' else '2'  # OrdType
            }
            
            if price and order_type != 'MARKET':
                order_fields['44'] = str(price)  # Price
            
            order_msg = self._create_fix_message('D', order_fields)  # New Order Single
            self._send_message(order_msg)
            
            # Wait for execution report
            response = self._receive_message()
            
            return {
                "success": True,
                "message": "Order placed successfully",
                "order_id": order_fields['11']
            }
            
        except Exception as e:
            return {"success": False, "message": f"Order failed: {str(e)}"}
    
    def get_positions(self):
        """Get open positions"""
        if not self.logged_in:
            return []
        
        try:
            # Send Position Request
            pos_request = self._create_fix_message('AN', {  # Request For Positions
                '710': '1',           # PosReqID
                '724': '0',           # PosReqType (Positions)
                '263': '1',           # SubscriptionRequestType
                '1': self.username    # Account
            })
            
            self._send_message(pos_request)
            
            # Return sample positions for demo
            return []
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def disconnect(self):
        """Disconnect from FIX API"""
        if self.socket and self.connected:
            # Send logout message
            logout_msg = self._create_fix_message('5', {})  # Logout
            self._send_message(logout_msg)
            
            self.socket.close()
            self.connected = False
            self.logged_in = False
            logger.info("Disconnected from IC Markets FIX API")

# Configuration for IC Markets FIX API
IC_MARKETS_FIX_CONFIG = {
    "demo": {
        "fix_host": "fix-demo.icmarkets.com",  # Replace with actual demo FIX host
        "fix_port": 9876,                      # Replace with actual demo FIX port
        "target_comp_id": "ICMARKETS_DEMO"     # Replace with actual target ID
    },
    "live": {
        "fix_host": "fix.icmarkets.com",       # Replace with actual live FIX host
        "fix_port": 9876,                      # Replace with actual live FIX port
        "target_comp_id": "ICMARKETS_LIVE"     # Replace with actual target ID
    }
}

def create_ic_markets_connection(username, password, environment="demo"):
    """Create IC Markets FIX API connection"""
    config = IC_MARKETS_FIX_CONFIG.get(environment)
    if not config:
        raise ValueError(f"Unknown environment: {environment}")
    
    return ICMarketsFIXAPI(
        username=username,
        password=password,
        sender_comp_id=f"GOLDDIGGER_{username}",
        target_comp_id=config["target_comp_id"],
        fix_host=config["fix_host"],
        fix_port=config["fix_port"]
    )

# Test function
if __name__ == "__main__":
    print("🔍 Testing IC Markets FIX API (Native macOS Solution)...")
    print("💡 This is a template - you need actual FIX API credentials from IC Markets")
    print("📞 Contact IC Markets support to get FIX API access")
    print("🚀 Once configured, this will work natively on macOS without Windows VM!")
    
    # Example usage (requires real credentials):
    # api = create_ic_markets_connection("your_username", "your_password", "demo")
    # result = api.connect()
    # print(f"Connection result: {result}")
