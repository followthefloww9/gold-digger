# Gold Digger AI Bot - Windows Setup Guide

## 🪟 Windows Users - Complete Setup Instructions

### Prerequisites
- **Windows 10/11** (64-bit)
- **Python 3.8+** (3.12+ recommended)
- **MetaTrader 5** installed and configured
- **Git** (optional, for cloning)

### 1. Download and Setup

```bash
# Clone or download the project
git clone <repository-url>
cd "Gold Digger"

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Windows-specific MT5 library
pip install MetaTrader5
```

### 2. Environment Configuration

Create `.env` file in project root:
```env
# Gemini AI API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# MT5 Configuration (Optional - auto-detected)
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# Trading Configuration
PAPER_TRADING=true
TRADING_AMOUNT=1000
RISK_PERCENTAGE=1.0
```

### 3. MetaTrader 5 Setup

1. **Install MT5**: Download from MetaQuotes website
2. **Login**: Configure your trading account
3. **Enable Algo Trading**: Tools → Options → Expert Advisors → Allow automated trading
4. **Python Integration**: Ensure MT5 Python API is enabled

### 4. Windows-Specific Features

#### Native MT5 Integration
- **Direct Connection**: Uses MetaTrader5 Python library
- **Real-time Data**: Live market feeds from MT5
- **Trade Execution**: Direct order placement through MT5
- **Account Management**: Full account information access

#### Windows MT5 REST Server (Optional)
For remote access or multi-machine setups:

```bash
# Start Windows MT5 REST server
cd windows_mt5_server
python mt5_rest_server.py

# Server will run on http://localhost:5000
# Provides REST API access to MT5 data
```

### 5. Running the Bot

#### Option 1: Streamlit Dashboard
```bash
# Activate virtual environment
venv\Scripts\activate

# Start the dashboard
streamlit run app.py

# Open browser to http://localhost:8501
```

#### Option 2: Background Service
```bash
# Activate virtual environment
venv\Scripts\activate

# Start background trading
python -c "
from core.simple_daemon import SimpleDaemon
daemon = SimpleDaemon()
daemon.start()
"
```

### 6. Windows Advantages

#### Full MT5 Integration
- ✅ **Native Library**: Direct MetaTrader5 Python integration
- ✅ **Real-time Data**: Live market feeds (no fallbacks needed)
- ✅ **Trade Execution**: Direct order placement
- ✅ **Account Info**: Full account details and history
- ✅ **Symbol Info**: Complete symbol specifications

#### Performance Benefits
- ✅ **Faster Data**: Direct MT5 connection (no API delays)
- ✅ **Lower Latency**: No network overhead for data
- ✅ **Reliable**: No dependency on external data sources
- ✅ **Complete Features**: All MT5 functionality available

#### Professional Trading
- ✅ **Live Trading**: Full live trading capabilities
- ✅ **Risk Management**: Complete position sizing
- ✅ **Order Management**: All order types supported
- ✅ **Portfolio Tracking**: Real-time P&L monitoring

### 7. Troubleshooting

#### Common Issues

**MT5 Connection Failed**
```bash
# Check MT5 is running
# Verify login credentials
# Enable automated trading in MT5
# Restart MT5 and try again
```

**Python Import Errors**
```bash
# Reinstall MetaTrader5 library
pip uninstall MetaTrader5
pip install MetaTrader5

# Check Python architecture matches MT5 (64-bit)
```

**Permission Errors**
```bash
# Run as Administrator if needed
# Check Windows Defender/Antivirus settings
# Ensure MT5 allows Python connections
```

### 8. Cross-Platform Compatibility

#### Windows → macOS/Linux
The bot includes a REST API server for cross-platform access:

1. **Windows Machine**: Run MT5 + REST server
2. **Other Platforms**: Connect via HTTP API
3. **Seamless Integration**: Same functionality across platforms

#### Configuration for Remote Access
```python
# In core/mt5_connector.py
MT5_REST_URL = "http://windows-machine-ip:5000"
USE_REST_API = True
```

### 9. Production Deployment

#### Windows Service (Advanced)
```bash
# Install as Windows service
pip install pywin32

# Create service wrapper
python setup_windows_service.py install

# Start service
net start GoldDiggerBot
```

#### Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (startup/daily)
4. Set action: Start program
5. Program: `python.exe`
6. Arguments: `app.py` or daemon script
7. Start in: Project directory

### 10. Security Considerations

#### API Keys
- Store in `.env` file (never commit to git)
- Use Windows Credential Manager for production
- Rotate keys regularly

#### MT5 Security
- Use demo accounts for testing
- Enable two-factor authentication
- Monitor account activity regularly

#### Network Security
- Use HTTPS for remote connections
- Configure firewall rules appropriately
- Use VPN for remote access

---

## 🎯 Windows Setup Complete!

Your Gold Digger AI Bot is now configured for optimal Windows performance with:
- ✅ Native MT5 integration
- ✅ Real-time market data
- ✅ Professional trading capabilities
- ✅ Cross-platform compatibility
- ✅ Production-ready deployment

**Ready for serious gold trading!** 🚀💰
