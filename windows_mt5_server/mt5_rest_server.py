#!/usr/bin/env python3
"""
Gold Digger AI Bot - Windows MT5 REST API Server
This runs on Windows VM/machine to provide MT5 access to macOS
Based on David _Detnator_'s solution from MQL5 forum
"""

from flask import Flask, jsonify, request
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global MT5 connection status
mt5_initialized = False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "MT5 REST API Bridge",
        "mt5_initialized": mt5_initialized,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/mt5/initialize', methods=['POST'])
def initialize_mt5():
    """Initialize MT5 connection"""
    global mt5_initialized
    
    try:
        if not mt5.initialize():
            return jsonify({
                "success": False,
                "message": f"MT5 initialization failed: {mt5.last_error()}"
            })
        
        mt5_initialized = True
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        account_info = mt5.account_info()
        
        return jsonify({
            "success": True,
            "message": "MT5 initialized successfully",
            "terminal_info": {
                "company": terminal_info.company if terminal_info else "Unknown",
                "name": terminal_info.name if terminal_info else "Unknown",
                "path": terminal_info.path if terminal_info else "Unknown"
            },
            "account_info": {
                "login": account_info.login if account_info else 0,
                "server": account_info.server if account_info else "Unknown",
                "balance": account_info.balance if account_info else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error initializing MT5: {str(e)}"
        })

@app.route('/mt5/account', methods=['GET'])
def get_account_info():
    """Get MT5 account information"""
    if not mt5_initialized:
        return jsonify({"success": False, "message": "MT5 not initialized"})
    
    try:
        account_info = mt5.account_info()
        if account_info is None:
            return jsonify({"success": False, "message": "Failed to get account info"})
        
        return jsonify({
            "success": True,
            "account": {
                "login": account_info.login,
                "trade_mode": account_info.trade_mode,
                "name": account_info.name,
                "server": account_info.server,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "limit_orders": account_info.limit_orders,
                "margin_so_mode": account_info.margin_so_mode,
                "trade_allowed": account_info.trade_allowed,
                "trade_expert": account_info.trade_expert,
                "balance": account_info.balance,
                "credit": account_info.credit,
                "profit": account_info.profit,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "margin_free": account_info.margin_free,
                "margin_level": account_info.margin_level
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/mt5/rates', methods=['GET'])
def get_rates():
    """Get market rates data"""
    if not mt5_initialized:
        return jsonify({"success": False, "message": "MT5 not initialized"})
    
    try:
        symbol = request.args.get('symbol', 'XAUUSD')
        timeframe_str = request.args.get('timeframe', 'M5')
        count = int(request.args.get('count', 100))
        
        # Convert timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        timeframe = timeframe_map.get(timeframe_str, mt5.TIMEFRAME_M5)
        
        # Get rates
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        
        if rates is None:
            return jsonify({
                "success": False,
                "message": f"Failed to get rates for {symbol}: {mt5.last_error()}"
            })
        
        # Convert to list of dictionaries
        rates_list = []
        for rate in rates:
            rates_list.append({
                "time": int(rate['time']),
                "open": float(rate['open']),
                "high": float(rate['high']),
                "low": float(rate['low']),
                "close": float(rate['close']),
                "tick_volume": int(rate['tick_volume']),
                "spread": int(rate['spread']),
                "real_volume": int(rate['real_volume'])
            })
        
        return jsonify({
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe_str,
            "count": len(rates_list),
            "data": rates_list
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/mt5/order', methods=['POST'])
def place_order():
    """Place trading order"""
    if not mt5_initialized:
        return jsonify({"success": False, "message": "MT5 not initialized"})
    
    try:
        data = request.get_json()
        
        symbol = data.get('symbol', 'XAUUSD')
        order_type = data.get('order_type', 'BUY')
        volume = float(data.get('volume', 0.01))
        price = data.get('price')
        sl = data.get('sl')
        tp = data.get('tp')
        
        # Prepare order request
        if order_type.upper() == 'BUY':
            order_type_mt5 = mt5.ORDER_TYPE_BUY
            if price is None:
                price = mt5.symbol_info_tick(symbol).ask
        else:
            order_type_mt5 = mt5.ORDER_TYPE_SELL
            if price is None:
                price = mt5.symbol_info_tick(symbol).bid
        
        request_dict = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type_mt5,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Gold Digger AI Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if sl:
            request_dict["sl"] = float(sl)
        if tp:
            request_dict["tp"] = float(tp)
        
        # Send order
        result = mt5.order_send(request_dict)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                "success": False,
                "message": f"Order failed: {result.comment}",
                "retcode": result.retcode
            })
        
        return jsonify({
            "success": True,
            "message": "Order placed successfully",
            "order": {
                "ticket": result.order,
                "volume": result.volume,
                "price": result.price,
                "bid": result.bid,
                "ask": result.ask,
                "comment": result.comment
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/mt5/positions', methods=['GET'])
def get_positions():
    """Get open positions"""
    if not mt5_initialized:
        return jsonify({"success": False, "message": "MT5 not initialized"})
    
    try:
        positions = mt5.positions_get()
        
        if positions is None:
            return jsonify({"success": True, "positions": []})
        
        positions_list = []
        for pos in positions:
            positions_list.append({
                "ticket": pos.ticket,
                "time": pos.time,
                "type": pos.type,
                "magic": pos.magic,
                "identifier": pos.identifier,
                "reason": pos.reason,
                "volume": pos.volume,
                "price_open": pos.price_open,
                "sl": pos.sl,
                "tp": pos.tp,
                "price_current": pos.price_current,
                "swap": pos.swap,
                "profit": pos.profit,
                "symbol": pos.symbol,
                "comment": pos.comment,
                "external_id": pos.external_id
            })
        
        return jsonify({
            "success": True,
            "positions": positions_list
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/mt5/close/<int:ticket>', methods=['POST'])
def close_position(ticket):
    """Close position by ticket"""
    if not mt5_initialized:
        return jsonify({"success": False, "message": "MT5 not initialized"})
    
    try:
        # Get position info
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return jsonify({"success": False, "message": "Position not found"})
        
        position = positions[0]
        
        # Prepare close request
        if position.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(position.symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).ask
        
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Gold Digger AI Bot - Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(close_request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                "success": False,
                "message": f"Close failed: {result.comment}",
                "retcode": result.retcode
            })
        
        return jsonify({
            "success": True,
            "message": "Position closed successfully",
            "result": {
                "ticket": result.order,
                "volume": result.volume,
                "price": result.price
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the server"""
    mt5.shutdown()
    return jsonify({"message": "Server shutting down"})

if __name__ == '__main__':
    print("🚀 Starting MT5 REST API Server for macOS Bridge...")
    print("📍 This server runs on Windows with MT5 installed")
    print("🔗 macOS Gold Digger bot connects via REST API")
    print("🌐 Server will be available at: http://0.0.0.0:8080")
    
    # Initialize MT5 on startup
    if mt5.initialize():
        mt5_initialized = True
        print("✅ MT5 initialized successfully")
        
        account_info = mt5.account_info()
        if account_info:
            print(f"📊 Account: {account_info.login} on {account_info.server}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
    else:
        print("❌ MT5 initialization failed")
        print("💡 Make sure MT5 is installed and running")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=8080, debug=False)
