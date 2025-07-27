# Gold Digger AI Bot Development Plan v2.0
*Compliant & Self-Reliant Trading System*

## Executive Summary

**Goal:** Automate a rule-based gold (XAU/USD) scalping strategy using an AI decision engine for trade validation and direct broker connection for execution. This revised plan eliminates reliance on third-party charting platform webhooks to ensure full compliance with service terms.

### Key Benefits
- Faster reaction to market moves with fully integrated system
- Consistent discipline by programmatically enforcing all trading rules
- 24/5 operation with real-time risk adjustments
- **Compliance:** Avoids violation of third-party terms of service by generating signals internally

### Core Components
1. **Data Feed & Signal Generation:** Direct data feed from MetaTrader 5, with strategy logic and indicators coded in Python
2. **Decision Engine:** Google Gemini API with structured prompts for trade validation
3. **Order Execution:** MetaTrader 5 via its native Python API

## Market & Strategy Rationale

### Why Gold (XAU/USD)?
- High liquidity and clear volatility spikes, ideal for scalping
- Well-documented order flow behavior

### Smart Money Concepts (SMC)
- **Order Blocks (OB):** Key support/resistance zones
- **Break of Structure (BOS):** Trend confirmation signals
- **Liquidity Grabs:** Market manipulation identification
- **Fair Value Gaps (FVG):** Imbalance areas for entries

### Strategy Workflow
1. Identify liquidity grab beyond a previous swing
2. Mark Order Block on H1/M15 for context
3. Await Break of Structure on M1/M5 to confirm directional bias
4. Enter on retest of OB or FVG with rejection candle
5. **Stop Loss:** Beyond OB extreme (+3-7 pips)
6. **Take Profit:** 1:2 RR or next session high/low/VWAP

## System Architecture & Data Flow

```
MT5 Broker Data Feed → Python Signal Generator → Google Gemini API → MT5 Execution → MT5 Broker
                            ↓                          ↓              ↓
                         Logs & Dashboard ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

### Components Breakdown

#### 1. MT5 Data Feed (Input)
- Uses `MetaTrader5` Python package for real-time and historical price data
- Direct connection to broker's server for XAU/USD data

#### 2. Python Signal Generator (Core Module)
- Replaces Pine Script with native Python implementation
- Contains SMC indicator functions (Order Blocks, FVG, BOS, etc.)
- Uses pandas and numpy for price data processing
- Identifies trading setups according to strategy rules

#### 3. Google Gemini API (Decision Engine)
- Receives formatted data from Signal Generator
- Uses structured prompts with few-shot examples
- Returns JSON: `{"action": "buy/sell", "size": %, "SL": price, "TP": price}`

#### 4. MT5 Execution Module
- Reads decision JSON from Gemini
- Executes market/pending orders via MetaTrader5 package
- Manages SL/TP and trade lifecycle

## Technology Stack & Dependencies

| Layer | Technology/Library | Version | Notes |
|-------|-------------------|---------|--------|
| **Core Runtime** | Python | 3.12+ | Latest stable version |
| **Data & Execution** | MetaTrader5 | 5.0.45+ | Official MT5 Python API |
| **Data Processing** | pandas | 2.2.2+ | Data manipulation |
| **Numerical Computing** | numpy | 2.0.1+ | Mathematical operations |
| **Technical Analysis** | pandas-ta | 0.3.14b+ | Technical indicators library |
| **AI Engine** | google-generativeai | 0.7.2+ | **Official Google Gemini SDK** |
| **HTTP Client** | httpx | 0.27.0+ | Async HTTP requests |
| **API Framework** | FastAPI | 0.111.0+ | REST API endpoints |
| **ASGI Server** | uvicorn | 0.30.1+ | Production ASGI server |
| **Task Scheduling** | APScheduler | 3.10.4+ | Background task management |
| **Database ORM** | SQLAlchemy | 2.0.31+ | Database abstraction |
| **Database** | SQLite | Built-in | Development database |
| **Database (Prod)** | PostgreSQL | 16+ | Production database |
| **Dashboard** | Streamlit | 1.36.0+ | Real-time monitoring |
| **Visualization** | plotly | 5.22.0+ | Interactive charts |
| **Environment** | python-dotenv | 1.0.1+ | Environment variables |
| **Logging** | loguru | 0.7.2+ | Enhanced logging |
| **Testing** | pytest | 8.2.2+ | Unit testing framework |

### Installation Commands
```bash
# Core dependencies
pip install MetaTrader5==5.0.45
pip install pandas==2.2.2 numpy==2.0.1
pip install pandas-ta==0.3.14b0

# Google Gemini SDK (Official)
pip install google-generativeai==0.7.2

# Web framework
pip install fastapi==0.111.0 uvicorn==0.30.1
pip install httpx==0.27.0

# Database & ORM
pip install sqlalchemy==2.0.31
pip install psycopg2-binary==2.9.9  # For PostgreSQL

# Scheduling & Utilities
pip install apscheduler==3.10.4
pip install python-dotenv==1.0.1
pip install loguru==0.7.2

# Dashboard & Visualization
pip install streamlit==1.36.0
pip install plotly==5.22.0

# Development & Testing
pip install pytest==8.2.2
pip install black==24.4.2  # Code formatting
pip install ruff==0.5.0    # Linting
```

## Implementation Phases & Milestones

### Phase 1: Core Logic Porting & Paper Trading (3 weeks)

#### Week 1: Indicator Porting
- **Critical First Step:** Convert all Pine Script SMC indicators to Python functions
- Implement using pandas for data manipulation
- **Validation:** Compare Python output against TradingView charts for accuracy
- Test with historical MT5 data

#### Week 2: Integration & End-to-End Simulation
- Integrate Python Signal Generator with Google Gemini API
- Build main application loop:
  ```
  Fetch Data → Analyze with Python Indicators → Send to Gemini → Log Decision
  ```
- Implement paper trading simulation with database logging
- Test full cycle with mock orders

#### Week 3: Refinement & Health Checks
- Analyze logs for discrepancies and logical errors
- Fine-tune indicator parameters in Python code
- Add robust error handling for broker connection issues
- Implement health checks with APScheduler
- Performance optimization and memory management

### Phase 2: Live Demo & Risk Controls (2-3 weeks)

#### Week 4-5: Live Integration
- Connect Gemini responses to MT5 execution on demo account
- Implement SL/TP and trailing stop logic
- Build real-time monitoring dashboard with Streamlit
- Add performance metrics and trade analytics

#### Week 6: Safety & Monitoring
- Implement critical safeguards:
  - Daily maximum loss limits
  - Circuit breakers for unusual market conditions
  - Manual override functionality
  - Risk management alerts
- Comprehensive logging and audit trail
- Load testing and stability verification

## Recommended Brokers for Automated Trading

### Top Tier Brokers (Recommended)

#### 1. IC Markets ⭐ **HIGHLY RECOMMENDED**
- **Why Choose:** Consistently ranked #1 for MT5 trading with ultra-fast execution and excellent spreads
- **Automation Support:** Full EA (Expert Advisor) support, API access
- **Gold Trading:** XAU/USD spreads from 0.3 pips, excellent liquidity
- **Demo Account:** Unlimited demo accounts with realistic market simulation
- **Server Locations:** Equinix NY4 data center in New York for ultra-fast execution
- **Platforms:** MT4, MT5, cTrader
- **Regulation:** ASIC, CySEC, FSA
- **Demo Setup:** [IC Markets Demo Account](https://www.icmarkets.com/global/en/open-trading-account/demo)

#### 2. XM Group
- **Why Choose:** Excellent for beginners, strong regulatory backing
- **Automation Support:** Full MT5 EA support, API trading allowed
- **Gold Trading:** Competitive spreads, no requotes
- **Demo Account:** 30-day demo (renewable), $100,000 virtual balance
- **Platforms:** MT4, MT5, XM WebTrader
- **Regulation:** CySEC, ASIC, IFSC
- **Minimum Deposit:** $5 (micro accounts available)

#### 3. OANDA
- **Why Choose:** Advanced MT5 features with powerful trading tools
- **Automation Support:** Python API, MT5 EA support
- **Gold Trading:** Fractional unit trading, excellent for testing
- **Demo Account:** Unlimited time, realistic spreads
- **Platforms:** MT4, MT5, OANDA Trade
- **Regulation:** FCA, ASIC, CFTC
- **Special Feature:** Python REST API for advanced automation

### Alternative Options

#### 4. Pepperstone
- **Automation Support:** Full EA support, cTrader copy trading
- **Gold Trading:** Raw spreads from 0.0 pips + commission
- **Demo Account:** 30 days, extendable
- **Regulation:** ASIC, FCA, CySEC

#### 5. IG Group
- **Automation Support:** MT4 EA support, API available
- **Gold Trading:** DMA gold trading available
- **Demo Account:** 21 days, professional platform
- **Regulation:** FCA, ASIC, CFTC

### Broker Comparison Table

| Broker | Gold Spread | Demo Period | EA Support | API Access | Regulation | Best For |
|--------|-------------|-------------|------------|-------------|------------|----------|
| **IC Markets** | 0.3+ pips | Unlimited | ✅ Full | ✅ Yes | ASIC/CySEC | **Scalping & Speed** |
| XM Group | 0.4+ pips | 30 days | ✅ Full | ✅ Limited | CySEC/ASIC | Beginners |
| OANDA | 0.5+ pips | Unlimited | ✅ Full | ✅ Python API | FCA/ASIC | **API Trading** |
| Pepperstone | 0.2+ pips | 30 days | ✅ Full | ✅ Yes | ASIC/FCA | Raw spreads |
| IG Group | 0.6+ pips | 21 days | ✅ MT4 only | ✅ Yes | FCA/ASIC | Institutional |

### Recommended Testing Sequence

#### Phase 1: Initial Development (IC Markets)
```bash
# Demo Account Setup
Broker: IC Markets
Account Type: Raw Spread Demo
Platform: MetaTrader 5
Balance: $10,000 (virtual)
Leverage: 1:500
```

#### Phase 2: API Testing (OANDA)
```bash
# For Python API integration testing
Broker: OANDA
Account Type: Demo CFD
Platform: MT5 + Python API
Balance: $10,000 (virtual)
Special: Direct API access for testing
```

#### Phase 3: Live Demo Comparison
- Run parallel tests on both IC Markets and OANDA
- Compare execution speeds and slippage
- Validate strategy performance across brokers

### Account Setup Instructions

#### IC Markets Demo Setup
1. Visit: https://www.icmarkets.com/global/en/open-trading-account/demo
2. Choose: "Raw Spread" account type
3. Platform: MetaTrader 5
4. Leverage: 1:500 (recommended for gold trading)
5. Balance: $10,000
6. Download MT5 terminal and login

#### OANDA Demo Setup (For API Testing)
1. Visit: https://www.oanda.com/register/
2. Select: Demo account
3. Platform: MetaTrader 5
4. Additional: Sign up for API access (fxTrade API)
5. Download MT5 and configure API credentials

### Broker Integration Code Example

```python
# config/broker_config.py
BROKER_CONFIGS = {
    'ic_markets': {
        'server': 'ICMarkets-Demo',
        'login': 'your_demo_login',
        'password': 'your_demo_password',
        'symbol': 'XAUUSD',
        'point_value': 0.01,
        'min_lot': 0.01,
        'max_lot': 100.0
    },
    'oanda': {
        'server': 'Oanda-Demo',
        'login': 'your_demo_login', 
        'password': 'your_demo_password',
        'symbol': 'XAUUSD',
        'point_value': 0.01,
        'min_lot': 0.01,
        'max_lot': 50.0,
        'api_key': 'your_oanda_api_key'  # For API trading
    }
}
```

## Data Feeds & Operational Costs

### Monthly Operating Expenses
- **MT5 VPS Hosting:** $15-25/month (Windows VPS required)
- **Google Gemini API:** Variable usage-based pricing
  - Gemini 1.5 Flash: $0.075/$0.30 per 1M tokens (input/output)
  - Generous free tier available for initial development
- **Broker Costs:** $0 (Demo accounts are free)
- **TradingView:** $0 (No longer required for automation)

**Estimated Monthly Cost:** $15-35 (significantly reduced from original plan)

## Security & Risk Management

### Backtesting Requirements
- Use `backtrader` or custom backtesting framework
- Test Python-based strategy on 2+ years historical data
- Validate performance metrics against manual analysis
- Monte Carlo simulation for robustness testing

### Forward Testing Protocol
- Continuous paper trading for minimum 2 weeks
- Real-time performance monitoring
- Strategy parameter optimization based on live data
- Risk metrics tracking and alerting

### Live Trading Safeguards
- **Daily Maximum Loss:** Configurable limit with automatic shutdown
- **Circuit Breakers:** Halt trading during extreme volatility
- **Manual Override:** Emergency stop functionality
- **Position Sizing:** Dynamic risk-based sizing
- **Connection Monitoring:** Automatic reconnection logic
- **Audit Trail:** Complete trade history and decision logging

## Development Environment Setup

### Required Software
- **Operating System:** Windows 10/11 (for MT5 compatibility)
- **Python:** 3.12+ with virtual environment
- **MetaTrader 5:** Latest terminal version
- **Code Editor:** VS Code with Python extensions
- **Database:** PostgreSQL 16+ for production

### Environment Variables
```bash
# .env file structure
GEMINI_API_KEY=your_gemini_api_key
MT5_LOGIN=your_mt5_account
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_server
DATABASE_URL=postgresql://user:pass@localhost/golddigger
LOG_LEVEL=INFO
MAX_DAILY_LOSS=500
```

### Project Structure
```
gold-digger-ai/
├── src/
│   ├── core/
│   │   ├── data_feed.py          # MT5 data connection
│   │   ├── signal_generator.py   # SMC indicators
│   │   ├── decision_engine.py    # Gemini API integration
│   │   └── execution_engine.py   # MT5 order management
│   ├── indicators/
│   │   ├── order_blocks.py       # Order Block detection
│   │   ├── fair_value_gaps.py    # FVG identification
│   │   ├── break_of_structure.py # BOS detection
│   │   └── liquidity_grabs.py    # Liquidity analysis
│   ├── risk_management/
│   │   ├── position_sizing.py    # Dynamic sizing
│   │   ├── stop_loss.py          # SL management
│   │   └── circuit_breakers.py   # Safety mechanisms
│   ├── database/
│   │   ├── models.py             # SQLAlchemy models
│   │   └── operations.py         # Database operations
│   └── dashboard/
│       ├── streamlit_app.py      # Monitoring dashboard
│       └── charts.py             # Visualization components
├── tests/
├── config/
├── logs/
├── requirements.txt
└── README.md
```

## Success Metrics & KPIs

### Performance Targets
- **Win Rate:** >65% of trades profitable
- **Risk-Reward Ratio:** Minimum 1:2
- **Maximum Drawdown:** <10% of account
- **Daily Profit Target:** 1-3% of account
- **System Uptime:** >99.5% during market hours

### Monitoring Dashboard Metrics
- Real-time P&L tracking
- Trade execution latency
- Signal generation frequency
- Risk metrics and exposure
- System health indicators
- API usage and costs

This development plan provides a comprehensive roadmap for building a compliant, self-reliant Gold Digger AI trading bot using the latest technologies and Google's official Gemini SDK.