# Gold Digger AI Bot - Vibe Coding Implementation Plan
*Updated for July 2025 with latest dependencies*

## 🎯 Project Overview

**Goal**: Build a Python-based scalping bot for XAU/USD (Gold) that uses Smart Money Concepts (SMC) for signal generation, Gemini 2.5 Flash API for decision validation, and a Streamlit UI for monitoring and control.

**Target Timeline**: 3-4 hours from setup to paper trading

**Skill Level**: Beginner-friendly (No professional coding experience required)

## 🌟 Guiding Principles

- **Vibe Coding**: Build fast, see results immediately
- **UI First**: Visual interface from minute one
- **Iterative & Rapid**: Small cycles, quick wins
- **Paper Trading Focus**: Validate before risking real money

---

## 📋 Phase 0: Project Setup & Environment

### Step 0.0: Create Virtual Environment
**Purpose**: Isolate project dependencies from your system

**Agent Prompt**:
```
Create a Python virtual environment for our Gold Digger AI Bot project. Please:
1. Create a new directory called 'gold_digger_bot'
2. Navigate into this directory
3. Create a Python virtual environment named 'venv'
4. Activate the virtual environment
5. Show me the commands to run in my terminal
```

### Step 0.1: Create Project Structure
**Purpose**: Organize code for maintainability

**Agent Prompt**:
```
Create a clean project structure for our Gold Digger AI Bot. Please create:
- Main project folder: gold_digger_bot/
- Subfolders: core/, ui/, utils/, tests/
- Essential files: README.md, .gitignore, requirements.txt
Show me the exact folder structure and any initial files needed.
```

### Step 0.2: Install Updated Dependencies
**Purpose**: Set up all required libraries with 2025-compatible versions

**Agent Prompt**:
```
Create a requirements.txt file with the latest compatible versions (as of July 2025) for:
- streamlit (latest stable)
- pandas (latest stable)
- numpy (latest stable)
- plotly (latest stable)
- MetaTrader5 (latest stable)
- google-generativeai (latest stable)
- pandas-ta (latest stable)
- python-dotenv (for environment variables)
- requests (for API calls)

Ensure all versions are compatible with each other and include the exact version numbers. Then provide the pip install command.
```

---

## 🎨 Phase 1: UI & Broker Connection

### Step 1.1: Basic Streamlit UI Shell
**Purpose**: Get visual feedback immediately

**Agent Prompt**:
```
Create app.py in the root directory with a complete Streamlit application that includes:
1. Page configuration with wide layout and Gold Digger title
2. Main header: "🏆 Gold Digger AI Bot - Live Trading Dashboard"
3. Sidebar with bot controls (Start/Stop toggle, Settings)
4. Three main sections using columns:
   - Live Market Chart (left column, 70% width)
   - Bot Status & Metrics (right column, 30% width)
   - Trade History (full width bottom section)
5. Use modern Streamlit styling with containers and metrics
6. Add placeholder content for each section
7. Include a refresh mechanism every 15 seconds

Make it look professional and engaging from the start.
```

### Step 1.2: MetaTrader 5 Connection
**Purpose**: Connect to live market data

**Agent Prompt**:
```
Create core/mt5_connector.py with robust MetaTrader 5 integration:

1. initialize_mt5() function that:
   - Connects to MT5 terminal
   - Handles connection errors gracefully
   - Returns connection status and account info

2. get_market_data(symbol, timeframe, count) function that:
   - Fetches OHLCV data as pandas DataFrame
   - Handles timeframe conversion (M1, M5, M15, H1, D1)
   - Includes proper error handling
   - Returns clean, formatted data

3. get_account_info() function for account details
4. check_market_hours() function for trading session detection

Include comprehensive error handling and logging. Test the connection in app.py by displaying XAUUSD M5 data in a table.
```

### Step 1.3: Interactive Market Visualization
**Purpose**: See live market action in real-time

**Agent Prompt**:
```
Enhance app.py with advanced Plotly candlestick visualization:

1. Create an interactive candlestick chart for XAUUSD with:
   - Professional styling (dark theme, gold colors)
   - Volume subplot below main chart
   - Zoom, pan, and crosshair functionality
   - Real-time updates every 15 seconds
   - Loading indicators during data fetch

2. Add chart controls in sidebar:
   - Timeframe selector (M1, M5, M15, H1)
   - Number of candles to display
   - Chart refresh rate

3. Display live price ticker with:
   - Current price
   - Daily change/percentage
   - Bid/Ask spread
   - Last update timestamp

4. Handle data loading states and connection errors gracefully

Make the chart professional-looking and responsive.
```

---

## 📊 Phase 2: Smart Money Concepts (SMC) Implementation

### Step 2.1: Core Technical Indicators
**Purpose**: Foundation indicators for SMC analysis

**Agent Prompt**:
```
Create core/indicators.py with comprehensive indicator calculations:

1. add_basic_indicators(df) function that adds:
   - VWAP (Volume Weighted Average Price)
   - EMA_21, EMA_50, EMA_200 (Exponential Moving Averages)
   - RSI (Relative Strength Index)
   - ATR (Average True Range) for volatility

2. add_smc_indicators(df) function that adds:
   - High/Low levels for different timeframes
   - Pivot points calculation
   - Support/resistance levels
   - Price action patterns

3. Use pandas-ta library for calculations
4. Ensure all indicators handle missing data properly
5. Add data validation and error handling

Update app.py to display these indicators on the chart with proper styling (different colors, line styles). Make VWAP prominent as it's crucial for SMC.
```

### Step 2.2: Session-Based Liquidity Levels
**Purpose**: Identify key liquidity zones for SMC strategy

**Agent Prompt**:
```
Enhance core/indicators.py with session-based analysis:

1. get_session_levels(df, session_type) function that identifies:
   - Asian Session (00:00-08:00 UTC): High/Low levels
   - London Session (08:00-16:00 UTC): High/Low levels
   - New York Session (13:00-21:00 UTC): High/Low levels
   - Previous Day High/Low (PDH/PDL)
   - Weekly High/Low levels

2. detect_liquidity_grabs(df) function that identifies:
   - Stop hunts above/below session levels
   - False breakouts and reversals
   - Liquidity grab patterns

3. Add timezone handling for accurate session detection
4. Return structured data with price levels and timestamps

Update the chart to display:
- Horizontal lines for session levels
- Color-coded zones (Asian=blue, London=green, NY=red)
- Annotations when liquidity grabs occur
- Interactive tooltips with level information
```

### Step 2.3: Order Block Detection
**Purpose**: Core SMC concept - identify institutional order blocks

**Agent Prompt**:
```
Create advanced order block detection in core/indicators.py:

1. detect_order_blocks(df, timeframe='M15') function that identifies:
   - Bullish Order Blocks: Strong buying zones after bearish moves
   - Bearish Order Blocks: Strong selling zones after bullish moves
   - Fresh vs. Mitigated order blocks
   - Order block strength/quality scoring

2. Algorithm should detect:
   - Significant price imbalances (Fair Value Gaps)
   - Areas where price moved aggressively away
   - Zones likely to act as support/resistance
   - Multiple timeframe order blocks (M15, H1, H4)

3. Return structured data with:
   - Order block coordinates (top, bottom, left, right)
   - Type (bullish/bearish)
   - Strength score (1-10)
   - Status (fresh/tested/mitigated)
   - Timeframe origin

4. Implement order block validation rules:
   - Minimum size requirements
   - Respect/disrespect tracking
   - Age-based filtering

Update chart to display order blocks as semi-transparent rectangles:
- Green for bullish OBs
- Red for bearish OBs
- Different opacity based on strength
- Labels with OB details
```

### Step 2.4: Break of Structure (BOS) Detection
**Purpose**: Identify trend changes and confirm trade setups

**Agent Prompt**:
```
Implement Break of Structure detection in core/indicators.py:

1. detect_break_of_structure(df) function that identifies:
   - Higher Highs/Higher Lows (Bullish BOS)
   - Lower Highs/Lower Lows (Bearish BOS)
   - Structure break confirmations
   - Failed breaks (Stop hunts)

2. Algorithm features:
   - Swing point identification using pivot detection
   - Minimum structure requirements (price and time)
   - Multiple timeframe structure analysis
   - BOS strength classification

3. detect_change_of_character(df) function for:
   - Market character shifts
   - Trend transition points
   - Momentum changes

4. Return data structure with:
   - BOS type and direction
   - Break price level
   - Confirmation timestamp
   - Structure strength score
   - Previous structure levels

Update chart visualization:
- Vertical lines at BOS points
- Arrows indicating direction
- Annotations with BOS details
- Color coding for strength levels
- Alert system for real-time BOS detection
```

---

## 🤖 Phase 3: AI Decision Engine & Trade Management

### Step 3.1: Gemini API Integration
**Purpose**: AI-powered trade validation and decision making

**Agent Prompt**:
```
Create core/gemini_client.py with advanced AI integration:

1. GeminiClient class with methods:
   - initialize_client() with API key management
   - get_trade_decision(market_context) for trade analysis
   - get_risk_assessment(trade_setup) for risk evaluation
   - get_market_sentiment(price_action) for overall sentiment

2. Smart prompting system that sends:
   - Current market structure analysis
   - Order block status and quality
   - Session level interactions
   - Price action context
   - Risk/reward ratios

3. Expected JSON response format:
   ```json
   {
     "trade_decision": "BUY|SELL|HOLD",
     "confidence_score": 0.85,
     "entry_price": 1985.50,
     "stop_loss": 1980.00,
     "take_profit": 1995.00,
     "risk_reward_ratio": 2.0,
     "reasoning": "Bullish OB respected with BOS confirmation",
     "market_sentiment": "BULLISH|BEARISH|NEUTRAL"
   }
   ```

4. Include:
   - Comprehensive error handling
   - Rate limiting protection
   - Response validation
   - Fallback decision logic
   - API usage tracking

Add environment variable management for API keys using python-dotenv.
```

### Step 3.2: Trading Logic Engine
**Purpose**: Combine SMC signals with AI validation

**Agent Prompt**:
```
Create core/trading_engine.py with complete trading logic:

1. TradingEngine class with methods:
   - analyze_market_setup() - combines all SMC indicators
   - validate_trade_setup() - checks entry criteria
   - calculate_position_size() - risk management
   - execute_trade_decision() - handles trade execution

2. Trade setup validation rules:
   - Liquidity grab + Order block respect + BOS confirmation
   - Multiple timeframe alignment
   - Risk/reward minimum ratios (1:2 minimum)
   - Market session filtering
   - Economic news avoidance

3. Risk management features:
   - Position sizing based on account balance
   - Maximum daily loss limits
   - Consecutive loss protection
   - Correlation filters for multiple trades

4. Real-time monitoring system:
   - Continuous market scanning
   - Setup quality scoring
   - Trade opportunity alerts
   - Performance tracking

Integrate with app.py to show:
- Real-time trade setups
- Setup quality scores
- AI decision reasoning
- Risk metrics dashboard
- Trade alerts and notifications
```

### Step 3.3: Paper Trading Execution
**Purpose**: Execute trades safely on demo account

**Agent Prompt**:
```
Enhance core/mt5_connector.py with complete trading functionality:

1. Trading execution functions:
   - open_trade(symbol, trade_type, volume, sl, tp, comment)
   - close_trade(ticket_number)
   - modify_trade(ticket, new_sl, new_tp)
   - get_open_positions()
   - get_trade_history()

2. Position management:
   - Real-time P&L tracking
   - Stop loss/take profit management
   - Trailing stop functionality
   - Partial close capabilities

3. Risk controls:
   - Maximum position size limits
   - Daily drawdown limits
   - Margin requirement checks
   - Correlation-based position limits

4. Trade logging:
   - Complete trade records
   - Entry/exit reasoning
   - Performance metrics
   - Error logging

Update app.py with trading dashboard:
- Live positions table
- P&L metrics and charts
- Trade execution buttons
- Position management controls
- Risk monitoring alerts
- Trade history with filtering

Include comprehensive error handling and connection recovery.
```

---

## 📈 Phase 4: Backtesting & Performance Analysis

### Step 4.1: Comprehensive Backtesting System
**Purpose**: Validate strategy before live trading

**Agent Prompt**:
```
Create backtester.py with professional backtesting capabilities:

1. BacktestEngine class with features:
   - Historical data processing (1-6 months of M5 data)
   - Realistic spread and slippage simulation
   - Commission and swap calculations
   - Multiple timeframe analysis

2. Strategy simulation:
   - Apply all SMC indicators to historical data
   - Simulate AI decision process (with caching for speed)
   - Execute virtual trades with realistic conditions
   - Track all metrics throughout the test period

3. Performance analytics:
   - Total P&L and percentage returns
   - Win rate and profit factor
   - Maximum drawdown and recovery time
   - Sharpe ratio and other risk metrics
   - Trade distribution analysis
   - Monthly/weekly performance breakdown

4. Advanced reporting:
   - Equity curve visualization
   - Drawdown periods chart
   - Trade distribution histograms
   - Risk-adjusted returns
   - Comparison with buy-and-hold

5. Export capabilities:
   - PDF reports with charts
   - CSV data export
   - Excel-compatible formats
   - JSON results for API integration

Include command-line interface and Streamlit integration for easy use.
```

### Step 4.2: Strategy Optimization & Analysis
**Purpose**: Fine-tune parameters for maximum performance

**Agent Prompt**:
```
Create utils/optimizer.py for strategy optimization:

1. ParameterOptimizer class with:
   - Grid search optimization
   - Genetic algorithm optimization
   - Walk-forward analysis
   - Monte Carlo simulation

2. Optimizable parameters:
   - Order block detection sensitivity
   - BOS confirmation requirements
   - Risk/reward ratios
   - Position sizing rules
   - Time-based filters

3. Optimization metrics:
   - Risk-adjusted returns (Sharpe, Sortino)
   - Maximum drawdown constraints
   - Profit factor targets
   - Trade frequency preferences

4. Robustness testing:
   - Out-of-sample validation
   - Parameter stability analysis
   - Stress testing scenarios
   - Sensitivity analysis

5. Results visualization:
   - 3D parameter surface plots
   - Optimization progress charts
   - Parameter correlation heatmaps
   - Robustness test results

Integrate with main application for easy parameter tuning and strategy improvement.
```

---

## 🚀 Phase 5: Advanced Features & Deployment

### Step 5.1: Real-time Monitoring & Alerts
**Purpose**: Stay informed of bot performance and opportunities

**Agent Prompt**:
```
Create utils/monitoring.py with comprehensive monitoring:

1. AlertSystem class with:
   - Email notifications for trades and errors
   - Discord/Telegram bot integration
   - SMS alerts for critical events
   - Desktop notifications

2. Performance monitoring:
   - Real-time P&L tracking
   - Drawdown alerts
   - Performance degradation detection
   - System health monitoring

3. Market monitoring:
   - High-impact news detection
   - Volatility spike alerts
   - Correlation change notifications
   - Market regime change detection

4. Dashboard enhancements:
   - Real-time performance metrics
   - Alert history and management
   - System status indicators
   - Mobile-responsive design

Add configuration panel in Streamlit for alert preferences and thresholds.
```

### Step 5.2: Data Management & Logging
**Purpose**: Maintain comprehensive records and enable analysis

**Agent Prompt**:
```
Create utils/data_manager.py for robust data handling:

1. DataManager class with:
   - SQLite database for trade records
   - Historical data caching
   - Real-time data buffering
   - Data backup and recovery

2. Logging system:
   - Structured logging with levels
   - Trade execution logs
   - Error tracking and reporting
   - Performance metrics logging

3. Data analysis tools:
   - Trade journal with screenshots
   - Performance attribution analysis
   - Market condition correlation
   - Strategy effectiveness tracking

4. Export and import features:
   - Multiple format support
   - Automated backup scheduling
   - Cloud storage integration
   - Data visualization tools

Include data retention policies and privacy protection measures.
```

---

## 🔧 Technical Requirements & Setup

### Prerequisites
- **Python 3.9+** (Recommended: Python 3.11)
- **MetaTrader 5** desktop application
- **Demo trading account** (any MT5 broker)
- **Google AI Studio API key** (free tier available)
- **4GB+ RAM** for smooth operation

### System Compatibility
- **Windows**: Full support with MT5 integration
- **macOS**: Limited (MT5 via Wine/virtual machine)
- **Linux**: Limited (MT5 via Wine/virtual machine)

### Quick Start Commands
```bash
# 1. Create project directory
mkdir gold_digger_bot && cd gold_digger_bot

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
streamlit run app.py
```

### Environment Variables (.env file)
```
GEMINI_API_KEY=your_gemini_api_key_here
MT5_LOGIN=your_demo_account_login
MT5_PASSWORD=your_demo_account_password
MT5_SERVER=your_broker_server_name
ALERT_EMAIL=your_email@domain.com
DISCORD_WEBHOOK=your_discord_webhook_url
```

---

## 📚 Additional Resources

### Learning Materials
- **Smart Money Concepts**: ICT trading concepts and order flow
- **MetaTrader 5**: API documentation and trading guides
- **Streamlit**: Dashboard development tutorials
- **Google Gemini**: AI integration best practices

### Troubleshooting Guide
- **MT5 Connection Issues**: Check platform status and credentials
- **API Rate Limits**: Implement proper request throttling
- **Data Quality**: Validate data integrity and handle gaps
- **Performance Issues**: Optimize code and data structures

### Next Steps After Implementation
1. **Paper Trading**: Run for 2-4 weeks minimum
2. **Strategy Refinement**: Based on backtest and paper results
3. **Risk Assessment**: Comprehensive risk analysis
4. **Live Trading**: Start with minimal position sizes
5. **Continuous Improvement**: Regular strategy updates

---

## ⚠️ Important Disclaimers

- **Educational Purpose**: This bot is for learning and research
- **Risk Warning**: Trading involves substantial risk of loss
- **Demo First**: Always test thoroughly before live trading
- **No Guarantees**: Past performance doesn't predict future results
- **Professional Advice**: Consider consulting financial professionals

---

*Built with ❤️ for aspiring algorithmic traders*

**Ready to start building? Follow each phase step-by-step and you'll have your Gold Digger AI Bot running in just a few hours!**