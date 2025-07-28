# 🚀 MQL5 Expert Advisor Setup Guide

## Complete Cross-Platform Trading Automation Setup

This guide will help you set up the Gold Digger AI Bot with MQL5 Expert Advisor for automated trading on both **macOS** and **Windows**.

---

## 📋 Prerequisites

### For All Platforms:
- ✅ **MetaTrader 5** installed and running
- ✅ **Demo or Live trading account** with ICMarkets or compatible broker
- ✅ **Python 3.8+** with Gold Digger bot installed
- ✅ **Trading permissions** enabled in MT5

### Platform-Specific:
- **macOS**: MT5 via Wine/CrossOver (already working)
- **Windows**: Native MT5 installation

---

## 🔧 Installation Steps

### Step 1: Copy Expert Advisor to MT5

#### On macOS (Wine/CrossOver):
```bash
# Navigate to MT5 Experts directory
cd "/Users/$(whoami)/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts"

# Create Gold Digger directory
mkdir -p GoldDigger

# Copy the EA file
cp "/path/to/gold-digger/mql5/GoldDiggerEA.mq5" GoldDigger/
```

#### On Windows:
```cmd
# Navigate to MT5 Experts directory
cd "C:\Users\%USERNAME%\AppData\Roaming\MetaQuotes\Terminal\[TERMINAL_ID]\MQL5\Experts"

# Create Gold Digger directory
mkdir GoldDigger

# Copy the EA file
copy "C:\path\to\gold-digger\mql5\GoldDiggerEA.mq5" GoldDigger\
```

### Step 2: Compile Expert Advisor

1. **Open MetaTrader 5**
2. **Press F4** to open MetaEditor
3. **Navigate** to `Experts/GoldDigger/GoldDiggerEA.mq5`
4. **Press F7** to compile
5. **Verify** compilation success (no errors)

### Step 3: Setup Data Directory

The EA will automatically create data directories, but you can set custom paths:

#### Automatic Detection (Recommended):
- **Windows**: `C:\Users\Public\Documents\GoldDigger\`
- **macOS**: `/Users/Shared/GoldDigger/`
- **Fallback**: MT5 Files directory

#### Manual Setup:
```bash
# Create data directory
mkdir -p /Users/Shared/GoldDigger  # macOS
mkdir C:\Users\Public\Documents\GoldDigger  # Windows

# Set permissions (macOS)
chmod 755 /Users/Shared/GoldDigger
```

---

## ⚙️ Configuration

### Step 4: Configure Expert Advisor

1. **Drag EA** to chart (XAUUSD recommended)
2. **Configure parameters**:

```
📊 TRADING PARAMETERS:
├── LotSize: 0.01 (start small)
├── MaxRisk: 0.02 (2% per trade)
├── MagicNumber: 20250728
├── EnableTrading: true
├── PaperTrading: true (for testing)
└── SignalCheckInterval: 1000ms

📁 FILE PARAMETERS:
├── PythonSignalFile: gold_digger_signals.json
├── ResultsFile: gold_digger_results.json
└── DataPath: (leave empty for auto-detect)
```

3. **Enable AutoTrading** (Ctrl+E or toolbar button)
4. **Verify EA** is running (smiley face in top-right)

### Step 5: Test Python Integration

```python
# Test MQL5 bridge connection
from core.mql5_bridge import MQL5Bridge

# Initialize bridge
bridge = MQL5Bridge()

# Test connection
result = bridge.test_connection()
print(f"Connection: {'✅ Success' if result['success'] else '❌ Failed'}")
print(f"EA Running: {result['ea_running']}")
print(f"Data Path: {result['data_path']}")

# Send test signal
bridge.send_hold_signal("Connection test")

# Check results
import time
time.sleep(2)
status = bridge.get_account_status()
print(f"Account Status: {status}")
```

---

## 🧪 Testing

### Step 6: Paper Trading Test

1. **Ensure PaperTrading = true** in EA settings
2. **Run Python bot**:

```python
from core.trading_engine import TradingEngine

# Initialize with MQL5 bridge
engine = TradingEngine(use_mql5_bridge=True)

# Check MQL5 status
status = engine.get_mql5_status()
print(f"MQL5 Available: {status['available']}")
print(f"EA Running: {status.get('ea_running', False)}")

# Generate and execute test signal
# (This will be paper trading - no real money)
signal = {
    'signal': 'BUY',
    'confidence': 0.8,
    'entry_price': 3340.0,
    'stop_loss': 3320.0,
    'take_profit': 3380.0,
    'analysis': 'Test signal from Python'
}

result = engine.execute_trade_via_mql5(signal)
print(f"Execution: {'✅ Success' if result['success'] else '❌ Failed'}")
print(f"Message: {result['message']}")
```

### Step 7: Verify Communication

**Check these files are created**:
- ✅ `gold_digger_signals.json` (Python → MQL5)
- ✅ `gold_digger_results.json` (MQL5 → Python)

**Monitor MT5 Expert tab** for log messages:
```
🚀 Gold Digger EA v1.0 - Initializing...
✅ Gold Digger EA initialized successfully
📁 Signal file: /path/to/gold_digger_signals.json
📁 Results file: /path/to/gold_digger_results.json
🎯 Trading mode: PAPER
📝 PAPER BUY: 0.01 lots at 3340.00 | SL: 3320.00 | TP: 3380.00
```

---

## 🔄 Live Trading Setup

### Step 8: Enable Live Trading (After Testing)

1. **Verify paper trading** works perfectly
2. **Set PaperTrading = false** in EA
3. **Reduce lot sizes** for initial live testing
4. **Monitor closely** for first few trades

**⚠️ IMPORTANT SAFETY CHECKS:**
- ✅ Start with minimum lot sizes (0.01)
- ✅ Test on demo account first
- ✅ Verify stop losses are working
- ✅ Monitor for 24 hours before increasing size
- ✅ Have manual override ready

---

## 🛠️ Troubleshooting

### Common Issues:

**1. EA Not Receiving Signals:**
```bash
# Check file permissions
ls -la /Users/Shared/GoldDigger/  # macOS
dir C:\Users\Public\Documents\GoldDigger\  # Windows

# Verify Python can write files
python -c "
from core.mql5_bridge import MQL5Bridge
bridge = MQL5Bridge()
print(f'Data path: {bridge.data_path}')
bridge.send_hold_signal('Test')
print('Test signal sent')
"
```

**2. MT5 AutoTrading Disabled:**
- Press **Ctrl+E** to enable AutoTrading
- Check **Tools → Options → Expert Advisors**
- Verify **"Allow automated trading"** is checked

**3. File Access Issues:**
```bash
# macOS: Fix permissions
sudo chmod -R 755 /Users/Shared/GoldDigger/
sudo chown -R $(whoami) /Users/Shared/GoldDigger/

# Windows: Run as Administrator if needed
```

**4. EA Compilation Errors:**
- Ensure **MQL5 syntax** is correct
- Check **#include** paths
- Verify **Trade.mqh** library is available

### Debug Mode:

Enable detailed logging in EA:
```mql5
// Add to EA input parameters
input bool DebugMode = true;

// Add debug prints
if(DebugMode) Print("🔍 Debug: Signal received - ", signalContent);
```

---

## 📊 Monitoring

### Real-Time Monitoring:

**Python Side:**
```python
# Monitor MQL5 status
bridge = MQL5Bridge()
while True:
    status = bridge.get_account_status()
    print(f"Balance: ${status['balance']:.2f} | "
          f"Equity: ${status['equity']:.2f} | "
          f"Positions: {status['open_positions']}")
    time.sleep(5)
```

**MT5 Side:**
- Monitor **Expert** tab for EA logs
- Check **Trade** tab for positions
- Watch **Account** info for balance changes

### Performance Tracking:

The EA automatically logs:
- ✅ **Trade executions** (success/failure)
- ✅ **Account balance** changes
- ✅ **Signal processing** times
- ✅ **Error conditions** and recovery

---

## 🎯 Next Steps

1. **✅ Complete setup** following this guide
2. **✅ Test paper trading** thoroughly
3. **✅ Verify all signals** work correctly
4. **✅ Monitor for 24 hours** in paper mode
5. **✅ Gradually enable** live trading
6. **✅ Scale up** lot sizes carefully

**Your Gold Digger AI Bot is now ready for professional automated trading!** 🚀💰

---

## 📞 Support

If you encounter issues:
1. **Check logs** in MT5 Expert tab
2. **Verify file permissions** and paths
3. **Test Python bridge** connection
4. **Review this guide** step by step

**The system is designed to work seamlessly on both macOS and Windows with proper setup!** ✨
