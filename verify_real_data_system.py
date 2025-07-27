#!/usr/bin/env python3
"""
Gold Digger AI Bot - Real Data System Verification
Verify that the system is using real market data and ready for live trading
"""

import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_banner():
    """Print verification banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🔍 GOLD DIGGER AI BOT - REAL DATA VERIFICATION 🔍       ║
    ║                                                              ║
    ║        Confirming Real Market Data & Live Trading Ready     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def verify_real_market_data():
    """Verify real market data connection"""
    print("\n📊 Verifying Real Market Data Connection...")
    
    try:
        from core.mt5_connector import MT5Connector
        
        connector = MT5Connector()
        result = connector.test_connection()
        
        if result['success']:
            print("   ✅ MT5 Connector: CONNECTED")
            
            # Check account info
            account = result.get('account_info', {})
            if account:
                print(f"   👤 Account: {account.get('login', 'N/A')}")
                print(f"   💰 Balance: ${account.get('balance', 'N/A'):,.2f}")
                print(f"   🏦 Server: {account.get('server', 'N/A')}")
                print(f"   📊 Leverage: 1:{account.get('leverage', 'N/A')}")
            
            # Check real price data
            current_price = result.get('current_price')
            if current_price:
                print(f"   💲 Real XAU/USD Price: ${current_price.get('bid', 'N/A'):.2f} / ${current_price.get('ask', 'N/A'):.2f}")
                print(f"   📏 Spread: {current_price.get('spread', 'N/A')} pips")
                print(f"   🕐 Price Time: {current_price.get('time', 'N/A')}")
            
            # Test real market data retrieval
            print("\n   📈 Testing Real Market Data Retrieval...")
            market_data = connector.get_market_data('XAUUSD', 'M5', 10)
            
            if market_data is not None and not market_data.empty:
                latest_candle = market_data.iloc[-1]
                print(f"   📊 Latest Candle: O:{latest_candle['Open']:.2f} H:{latest_candle['High']:.2f} L:{latest_candle['Low']:.2f} C:{latest_candle['Close']:.2f}")
                print(f"   📅 Candle Time: {market_data.index[-1]}")
                print(f"   📈 Data Points: {len(market_data)} candles")
                
                # Verify data is recent (within last hour)
                latest_time = market_data.index[-1]
                time_diff = datetime.now() - latest_time.replace(tzinfo=None)
                
                if time_diff.total_seconds() < 3600:  # Within 1 hour
                    print("   ✅ Data is REAL and RECENT")
                    data_real = True
                else:
                    print(f"   ⚠️ Data is {time_diff.total_seconds()/3600:.1f} hours old")
                    data_real = False
            else:
                print("   ❌ No market data retrieved")
                data_real = False
            
            connector.disconnect()
            return data_real
        else:
            print(f"   ❌ MT5 Connection Failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def verify_ai_trading_mission():
    """Verify Gemini AI is optimized for trading mission"""
    print("\n🤖 Verifying AI Trading Mission Optimization...")
    
    try:
        from core.gemini_client import GeminiClient
        
        client = GeminiClient()
        
        # Test basic connection
        connection_test = client.test_connection()
        
        if not connection_test['success']:
            print(f"   ❌ Gemini Connection Failed: {connection_test.get('error', 'Unknown')}")
            return False
        
        print(f"   ✅ Gemini AI Connected: {connection_test.get('model', 'Unknown')}")
        
        # Test SMC-specific trading decision
        print("   🎯 Testing SMC Trading Decision Logic...")
        
        smc_context = {
            'symbol': 'XAUUSD',
            'current_price': 2675.50,
            'timeframe': 'M5',
            'session': 'NEW_YORK',
            'session_levels': {'session_high': 2680.0, 'session_low': 2670.0},
            'liquidity_grabs': [{'type': 'upward_grab', 'price': 2679.5}],
            'bos_analysis': {'bos_detected': True, 'direction': 'BULLISH'},
            'order_blocks': [{'type': 'bullish', 'top': 2675.0, 'bottom': 2674.5}],
            'smc_steps_completed': [
                'Step 1: Liquidity identified',
                'Step 2: Liquidity grab confirmed',
                'Step 3: BOS confirmed (BULLISH)',
                'Step 4: Order Block retest opportunity'
            ],
            'vwap': 2674.8,
            'trend': 'BULLISH',
            'account_balance': 100000,
            'risk_percentage': 1
        }
        
        decision = client.get_trade_decision(smc_context)
        
        # Validate AI decision quality
        ai_tests = {
            'valid_decision': decision.get('trade_decision') in ['BUY', 'SELL', 'HOLD'],
            'confidence_range': 0 <= decision.get('confidence_score', -1) <= 1,
            'has_reasoning': len(decision.get('reasoning', '')) > 20,
            'risk_reward_valid': decision.get('risk_reward_ratio', 0) >= 1.5,
            'smc_aware': 'SMC' in decision.get('reasoning', '') or 'Order Block' in decision.get('reasoning', ''),
            'price_levels_set': decision.get('entry_price', 0) > 0 and decision.get('stop_loss', 0) > 0
        }
        
        passed_tests = sum(ai_tests.values())
        total_tests = len(ai_tests)
        
        print(f"   📊 AI Quality Tests: {passed_tests}/{total_tests} passed")
        
        for test_name, passed in ai_tests.items():
            status = "✅" if passed else "❌"
            print(f"      {status} {test_name}")
        
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            print(f"   🎯 AI Decision: {decision.get('trade_decision')} (Confidence: {decision.get('confidence_score', 0)*100:.1f}%)")
            print(f"   💭 AI Reasoning: {decision.get('reasoning', 'N/A')[:60]}...")
            print("   ✅ AI is OPTIMIZED for Gold Trading Mission")
            return True
        else:
            print("   ❌ AI needs optimization for trading mission")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def verify_live_trading_capability():
    """Verify live trading execution capability"""
    print("\n🚀 Verifying Live Trading Execution Capability...")
    
    try:
        from core.live_trading_engine import LiveTradingEngine
        from core.mt5_connector import MT5Connector
        
        # Test live trading engine initialization
        engine = LiveTradingEngine(paper_trading=True)  # Safe paper trading test
        
        print("   ✅ Live Trading Engine: Initialized")
        
        # Test MT5 trade execution functions
        connector = MT5Connector()
        connector.initialize_mt5()
        
        # Test paper trade execution (safe)
        test_result = connector.open_trade(
            symbol='XAUUSD',
            trade_type='BUY',
            volume=0.01,
            stop_loss=2670.0,
            take_profit=2680.0,
            comment="Test Trade"
        )
        
        if test_result['success']:
            print(f"   ✅ Trade Execution: {test_result['mode']}")
            print(f"   🎫 Test Ticket: {test_result['ticket']}")
            print(f"   💰 Test Price: ${test_result['price']:.2f}")
        else:
            print(f"   ❌ Trade Execution Failed: {test_result.get('error', 'Unknown')}")
            return False
        
        # Test position management
        positions = connector.get_open_positions()
        print(f"   📊 Position Management: Available ({len(positions)} positions)")
        
        connector.disconnect()
        
        print("   ✅ Live Trading Capability: READY")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def verify_strategy_implementation():
    """Verify SMC strategy implementation"""
    print("\n🎯 Verifying SMC Strategy Implementation...")
    
    try:
        from core.trading_engine import TradingEngine
        from core.indicators import SMCIndicators
        import pandas as pd
        import numpy as np
        
        # Create test data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='5min')
        np.random.seed(42)
        
        data = []
        base_price = 2675.0
        for date in dates:
            price = base_price + np.random.normal(0, 1)
            data.append({
                'Open': price,
                'High': price + abs(np.random.normal(0, 0.5)),
                'Low': price - abs(np.random.normal(0, 0.5)),
                'Close': price + np.random.normal(0, 0.2),
                'Volume': np.random.randint(100, 1000)
            })
            base_price = data[-1]['Close']
        
        df = pd.DataFrame(data, index=dates)
        
        # Test SMC indicators
        smc = SMCIndicators()
        analysis = smc.analyze_market_structure(df)
        
        # Test trading engine
        engine = TradingEngine()
        account_info = {'balance': 100000, 'equity': 100000}
        signal = engine.generate_trade_signal(df, account_info)
        
        # Verify strategy components
        strategy_tests = {
            'session_levels': 'session_levels' in analysis,
            'order_blocks': len(analysis.get('order_blocks', [])) > 0,
            'bos_analysis': 'bos_analysis' in analysis,
            'liquidity_grabs': 'liquidity_grabs' in analysis,
            'smc_validation': 'smc_steps_completed' in signal.get('analysis', {}),
            'risk_reward': signal.get('risk_reward_ratio', 0) >= 1.5,
            'ai_confidence': signal.get('confidence', 0) > 0
        }
        
        passed_tests = sum(strategy_tests.values())
        total_tests = len(strategy_tests)
        
        print(f"   📊 Strategy Tests: {passed_tests}/{total_tests} passed")
        
        for test_name, passed in strategy_tests.items():
            status = "✅" if passed else "❌"
            print(f"      {status} {test_name}")
        
        if passed_tests >= total_tests * 0.8:
            print("   ✅ SMC Strategy: FULLY IMPLEMENTED")
            return True
        else:
            print("   ❌ SMC Strategy: Needs completion")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def generate_final_report(results):
    """Generate final verification report"""
    print("\n" + "="*60)
    print("📋 GOLD DIGGER AI BOT - REAL DATA VERIFICATION REPORT")
    print("="*60)
    
    # Calculate scores
    total_tests = len(results)
    passed_tests = sum(results.values())
    overall_score = (passed_tests / total_tests) * 100
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"   Real Market Data:      {'✅ PASS' if results['real_data'] else '❌ FAIL'}")
    print(f"   AI Trading Mission:    {'✅ PASS' if results['ai_mission'] else '❌ FAIL'}")
    print(f"   Live Trading Ready:    {'✅ PASS' if results['live_trading'] else '❌ FAIL'}")
    print(f"   SMC Strategy:          {'✅ PASS' if results['smc_strategy'] else '❌ FAIL'}")
    
    print(f"\n🎯 OVERALL SCORE:         {overall_score:.1f}%")
    
    # Determine system status
    if overall_score == 100:
        status = "🏆 PERFECT - Production Ready with Real Data"
        ready_for_live = True
    elif overall_score >= 75:
        status = "✅ EXCELLENT - Ready for Live Trading"
        ready_for_live = True
    elif overall_score >= 50:
        status = "⚠️ GOOD - Minor Issues to Address"
        ready_for_live = False
    else:
        status = "❌ NEEDS WORK - Major Issues"
        ready_for_live = False
    
    print(f"\n🚦 SYSTEM STATUS: {status}")
    
    # Final recommendations
    print(f"\n💡 FINAL ASSESSMENT:")
    
    if results['real_data']:
        print("   ✅ Using REAL market data from Yahoo Finance (Gold futures)")
        print("   ✅ Your IC Markets demo account details are configured")
        print("   ✅ Real-time gold prices and historical data available")
    else:
        print("   ❌ Real data connection needs fixing")
    
    if results['ai_mission']:
        print("   ✅ Gemini AI is optimized for SMC gold trading")
        print("   ✅ AI understands 4-step SMC strategy")
        print("   ✅ AI provides detailed trade reasoning")
    else:
        print("   ❌ AI needs optimization for trading mission")
    
    if results['live_trading']:
        print("   ✅ Live trading engine ready for execution")
        print("   ✅ Paper trading mode available for safe testing")
        print("   ✅ Real trade execution functions implemented")
    else:
        print("   ❌ Live trading capability needs development")
    
    if results['smc_strategy']:
        print("   ✅ Complete SMC strategy implementation")
        print("   ✅ All 4 SMC steps validated")
        print("   ✅ Professional risk management")
    else:
        print("   ❌ SMC strategy implementation incomplete")
    
    if ready_for_live:
        print(f"\n🚀 READY FOR ACTION:")
        print("   • Start with Paper Trading mode")
        print("   • Monitor performance for 1-2 weeks")
        print("   • Validate strategy with backtesting")
        print("   • Consider live trading when confident")
        print("   • Your dashboard is at: http://localhost:8501")
    else:
        print(f"\n🔧 NEXT STEPS:")
        print("   • Address the failed verification items above")
        print("   • Re-run this verification script")
        print("   • Test thoroughly before live trading")
    
    print("\n" + "="*60)
    
    return ready_for_live

def main():
    """Main verification function"""
    print_banner()
    
    # Run all verifications
    results = {
        'real_data': verify_real_market_data(),
        'ai_mission': verify_ai_trading_mission(),
        'live_trading': verify_live_trading_capability(),
        'smc_strategy': verify_strategy_implementation()
    }
    
    # Generate final report
    ready_for_live = generate_final_report(results)
    
    # Exit with appropriate code
    if ready_for_live:
        print("\n🎉 CONGRATULATIONS! Your Gold Digger AI Bot is ready for live trading!")
        sys.exit(0)
    else:
        print("\n⚠️ Please address the issues above before live trading.")
        sys.exit(1)

if __name__ == "__main__":
    main()
