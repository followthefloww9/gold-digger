"""
Gold Digger AI Bot - Data Management
Database operations for trade history, performance tracking, and analytics
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """
    Comprehensive data management for trading bot
    Handles trade history, performance metrics, and analytics storage
    """
    
    def __init__(self, db_path: str = "gold_digger.db"):
        """Initialize data manager with SQLite database"""
        self.db_path = db_path
        self.connection = None
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
        logger.info(f"DataManager initialized with database: {db_path}")
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Trades table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        entry_time DATETIME,
                        exit_time DATETIME,
                        symbol TEXT DEFAULT 'XAUUSD',
                        direction TEXT,
                        entry_price REAL,
                        exit_price REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        lot_size REAL,
                        pnl REAL,
                        status TEXT,
                        confidence REAL,
                        setup_quality INTEGER,
                        smc_steps TEXT,
                        reasoning TEXT,
                        session TEXT,
                        timeframe TEXT
                    )
                """)
                
                # Performance metrics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE UNIQUE,
                        daily_pnl REAL,
                        cumulative_pnl REAL,
                        trades_count INTEGER,
                        winning_trades INTEGER,
                        losing_trades INTEGER,
                        win_rate REAL,
                        max_drawdown REAL,
                        account_balance REAL,
                        risk_utilization REAL
                    )
                """)
                
                # Market analysis table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        timeframe TEXT,
                        current_price REAL,
                        trend TEXT,
                        session TEXT,
                        order_blocks_count INTEGER,
                        bos_detected BOOLEAN,
                        liquidity_grabs_count INTEGER,
                        vwap REAL,
                        rsi REAL,
                        atr REAL,
                        setup_quality INTEGER,
                        ai_confidence REAL,
                        analysis_data TEXT
                    )
                """)
                
                # System events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT,
                        severity TEXT,
                        message TEXT,
                        details TEXT
                    )
                """)

                # Bot state table for persistence across sessions
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_state (
                        id INTEGER PRIMARY KEY,
                        is_running BOOLEAN DEFAULT FALSE,
                        trading_mode TEXT DEFAULT 'Paper Trading',
                        risk_percentage REAL DEFAULT 1.0,
                        max_risk_amount REAL DEFAULT 1000.0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT,
                        configuration TEXT
                    )
                """)

                # Initialize default bot state if not exists
                conn.execute("""
                    INSERT OR IGNORE INTO bot_state (id, is_running, trading_mode, risk_percentage, max_risk_amount)
                    VALUES (1, FALSE, 'Paper Trading', 1.0, 1000.0)
                """)
                
                conn.commit()
                logger.info("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def save_trade(self, trade_data: Dict) -> bool:
        """
        Save trade record to database
        
        Args:
            trade_data: Trade information dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prepare trade data
                smc_steps = json.dumps(trade_data.get('smc_steps', []))
                
                conn.execute("""
                    INSERT INTO trades (
                        entry_time, exit_time, direction, entry_price, exit_price,
                        stop_loss, take_profit, lot_size, pnl, status,
                        confidence, setup_quality, smc_steps, reasoning,
                        session, timeframe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data.get('entry_time'),
                    trade_data.get('exit_time'),
                    trade_data.get('direction'),
                    trade_data.get('entry_price'),
                    trade_data.get('exit_price'),
                    trade_data.get('stop_loss'),
                    trade_data.get('take_profit'),
                    trade_data.get('lot_size'),
                    trade_data.get('pnl'),
                    trade_data.get('status'),
                    trade_data.get('confidence'),
                    trade_data.get('setup_quality'),
                    smc_steps,
                    trade_data.get('reasoning'),
                    trade_data.get('session'),
                    trade_data.get('timeframe')
                ))
                
                conn.commit()
                logger.info(f"Trade saved: {trade_data.get('direction')} at {trade_data.get('entry_price')}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving trade: {str(e)}")
            return False
    
    def get_trade_history(self, days: int = 30, limit: int = 100) -> pd.DataFrame:
        """
        Get trade history from database
        
        Args:
            days: Number of days to look back
            limit: Maximum number of trades to return
            
        Returns:
            DataFrame with trade history
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM trades 
                    WHERE entry_time >= date('now', '-{} days')
                    ORDER BY entry_time DESC 
                    LIMIT {}
                """.format(days, limit)
                
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    # Parse JSON fields
                    df['smc_steps'] = df['smc_steps'].apply(
                        lambda x: json.loads(x) if x else []
                    )
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting trade history: {str(e)}")
            return pd.DataFrame()

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """
        Get recent trades from database

        Args:
            limit: Maximum number of trades to return

        Returns:
            List of trade dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT * FROM trades
                ORDER BY entry_time DESC
                LIMIT ?
                """

                cursor = conn.execute(query, (limit,))
                rows = cursor.fetchall()

                if not rows:
                    return []

                # Get column names
                columns = [description[0] for description in cursor.description]

                # Convert to list of dictionaries
                trades = []
                for row in rows:
                    trade_dict = dict(zip(columns, row))

                    # Convert datetime strings to datetime objects
                    trade_dict['entry_time'] = pd.to_datetime(trade_dict['entry_time'])
                    if trade_dict['exit_time']:
                        trade_dict['exit_time'] = pd.to_datetime(trade_dict['exit_time'])

                    trades.append(trade_dict)

                return trades

        except Exception as e:
            logger.error(f"Error getting recent trades: {str(e)}")
            return []

    def save_performance_metrics(self, date: str, metrics: Dict) -> bool:
        """
        Save daily performance metrics
        
        Args:
            date: Date in YYYY-MM-DD format
            metrics: Performance metrics dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO performance_metrics (
                        date, daily_pnl, cumulative_pnl, trades_count,
                        winning_trades, losing_trades, win_rate,
                        max_drawdown, account_balance, risk_utilization
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date,
                    metrics.get('daily_pnl'),
                    metrics.get('cumulative_pnl'),
                    metrics.get('trades_count'),
                    metrics.get('winning_trades'),
                    metrics.get('losing_trades'),
                    metrics.get('win_rate'),
                    metrics.get('max_drawdown'),
                    metrics.get('account_balance'),
                    metrics.get('risk_utilization')
                ))
                
                conn.commit()
                logger.info(f"Performance metrics saved for {date}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving performance metrics: {str(e)}")
            return False
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, any]:
        """
        Get performance summary for specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance summary dictionary
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get trades for the period
                trades_query = """
                    SELECT * FROM trades 
                    WHERE entry_time >= date('now', '-{} days')
                    AND status IN ('TAKE_PROFIT', 'STOP_LOSS', 'FORCED_CLOSE')
                """.format(days)
                
                trades_df = pd.read_sql_query(trades_query, conn)
                
                if trades_df.empty:
                    return self._get_empty_performance_summary()
                
                # Calculate metrics
                total_trades = len(trades_df)
                winning_trades = len(trades_df[trades_df['pnl'] > 0])
                losing_trades = len(trades_df[trades_df['pnl'] <= 0])
                
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                total_pnl = trades_df['pnl'].sum()
                avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
                avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
                
                profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
                
                # Get daily performance
                daily_query = """
                    SELECT * FROM performance_metrics 
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date
                """.format(days)
                
                daily_df = pd.read_sql_query(daily_query, conn)
                
                max_drawdown = daily_df['max_drawdown'].max() if not daily_df.empty else 0
                current_balance = daily_df['account_balance'].iloc[-1] if not daily_df.empty else 100000
                
                return {
                    'period_days': days,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'profit_factor': round(profit_factor, 2),
                    'max_drawdown': round(max_drawdown, 2),
                    'current_balance': round(current_balance, 2),
                    'daily_performance': daily_df.to_dict('records') if not daily_df.empty else [],
                    'recent_trades': trades_df.tail(10).to_dict('records')
                }
                
        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            return self._get_empty_performance_summary()
    
    def save_market_analysis(self, analysis_data: Dict) -> bool:
        """
        Save market analysis data
        
        Args:
            analysis_data: Market analysis dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Serialize complex data
                analysis_json = json.dumps({
                    'order_blocks': analysis_data.get('order_blocks', []),
                    'bos_analysis': analysis_data.get('bos_analysis', {}),
                    'liquidity_grabs': analysis_data.get('liquidity_grabs', []),
                    'session_levels': analysis_data.get('session_levels', {}),
                    'indicators': analysis_data.get('indicators', {})
                })
                
                conn.execute("""
                    INSERT INTO market_analysis (
                        timeframe, current_price, trend, session,
                        order_blocks_count, bos_detected, liquidity_grabs_count,
                        vwap, rsi, atr, setup_quality, ai_confidence, analysis_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data.get('timeframe', 'M5'),
                    analysis_data.get('current_price'),
                    analysis_data.get('trend'),
                    analysis_data.get('session'),
                    len(analysis_data.get('order_blocks', [])),
                    analysis_data.get('bos_analysis', {}).get('bos_detected', False),
                    len(analysis_data.get('liquidity_grabs', [])),
                    analysis_data.get('indicators', {}).get('vwap'),
                    analysis_data.get('indicators', {}).get('rsi'),
                    analysis_data.get('indicators', {}).get('atr'),
                    analysis_data.get('setup_quality'),
                    analysis_data.get('ai_confidence'),
                    analysis_json
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving market analysis: {str(e)}")
            return False
    
    def log_system_event(self, event_type: str, severity: str, message: str, details: Dict = None) -> bool:
        """
        Log system event
        
        Args:
            event_type: Type of event (TRADE, ERROR, WARNING, INFO)
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            message: Event message
            details: Additional event details
            
        Returns:
            True if logged successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                details_json = json.dumps(details) if details else None
                
                conn.execute("""
                    INSERT INTO system_events (event_type, severity, message, details)
                    VALUES (?, ?, ?, ?)
                """, (event_type, severity, message, details_json))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")
            return False
    
    def get_system_events(self, hours: int = 24, severity: str = None) -> pd.DataFrame:
        """
        Get recent system events
        
        Args:
            hours: Number of hours to look back
            severity: Filter by severity level
            
        Returns:
            DataFrame with system events
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM system_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                """.format(hours)
                
                if severity:
                    query += f" AND severity = '{severity}'"
                
                query += " ORDER BY timestamp DESC LIMIT 100"
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"Error getting system events: {str(e)}")
            return pd.DataFrame()
    
    def _get_empty_performance_summary(self) -> Dict[str, any]:
        """Return empty performance summary"""
        return {
            'period_days': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'current_balance': 100000.0,
            'daily_performance': [],
            'recent_trades': []
        }
    
    def export_data(self, export_path: str, tables: List[str] = None) -> bool:
        """
        Export database data to CSV files
        
        Args:
            export_path: Directory path for export files
            tables: List of tables to export (None for all)
            
        Returns:
            True if exported successfully
        """
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            if tables is None:
                tables = ['trades', 'performance_metrics', 'market_analysis', 'system_events']
            
            with sqlite3.connect(self.db_path) as conn:
                for table in tables:
                    try:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                        if not df.empty:
                            export_file = export_dir / f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            df.to_csv(export_file, index=False)
                            logger.info(f"Exported {table} to {export_file}")
                    except Exception as e:
                        logger.error(f"Error exporting {table}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """
        Clean up old data to maintain database performance
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            True if cleanup successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clean old market analysis (keep less detailed data)
                conn.execute("""
                    DELETE FROM market_analysis 
                    WHERE timestamp < date('now', '-{} days')
                """.format(days_to_keep))
                
                # Clean old system events (keep only critical events)
                conn.execute("""
                    DELETE FROM system_events 
                    WHERE timestamp < date('now', '-{} days')
                    AND severity NOT IN ('HIGH', 'CRITICAL')
                """.format(days_to_keep))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True
                
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            return False

    def save_bot_state(self, is_running: bool, trading_mode: str, risk_percentage: float,
                      max_risk_amount: float, session_id: str = None, configuration: dict = None) -> bool:
        """
        Save bot state to database for persistence across sessions

        Args:
            is_running: Whether bot is currently running
            trading_mode: 'Paper Trading' or 'Live Trading'
            risk_percentage: Risk percentage per trade
            max_risk_amount: Maximum risk amount per trade
            session_id: Optional session identifier
            configuration: Optional additional configuration

        Returns:
            True if saved successfully
        """
        try:
            config_json = json.dumps(configuration) if configuration else None

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE bot_state SET
                        is_running = ?,
                        trading_mode = ?,
                        risk_percentage = ?,
                        max_risk_amount = ?,
                        last_updated = CURRENT_TIMESTAMP,
                        session_id = ?,
                        configuration = ?
                    WHERE id = 1
                """, (is_running, trading_mode, risk_percentage, max_risk_amount, session_id, config_json))

                conn.commit()
                logger.info(f"Bot state saved: Running={is_running}, Mode={trading_mode}")
                return True

        except Exception as e:
            logger.error(f"Error saving bot state: {str(e)}")
            return False

    def get_bot_state(self) -> Dict:
        """
        Get current bot state from database

        Returns:
            Dictionary with bot state information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT is_running, trading_mode, risk_percentage, max_risk_amount,
                           last_updated, session_id, configuration
                    FROM bot_state WHERE id = 1
                """)

                row = cursor.fetchone()
                if row:
                    config = json.loads(row[6]) if row[6] else {}
                    return {
                        'is_running': bool(row[0]),
                        'trading_mode': row[1],
                        'risk_percentage': row[2],
                        'max_risk_amount': row[3],
                        'last_updated': row[4],
                        'session_id': row[5],
                        'configuration': config
                    }
                else:
                    # Return default state
                    return {
                        'is_running': False,
                        'trading_mode': 'Paper Trading',
                        'risk_percentage': 1.0,
                        'max_risk_amount': 1000.0,
                        'last_updated': None,
                        'session_id': None,
                        'configuration': {}
                    }

        except Exception as e:
            logger.error(f"Error getting bot state: {str(e)}")
            return {
                'is_running': False,
                'trading_mode': 'Paper Trading',
                'risk_percentage': 1.0,
                'max_risk_amount': 1000.0,
                'last_updated': None,
                'session_id': None,
                'configuration': {}
            }

# Test function
def test_data_manager():
    """Test data manager functionality"""
    print("🔍 Testing Data Manager...")
    
    # Create data manager
    dm = DataManager("test_gold_digger.db")
    
    # Test trade saving
    sample_trade = {
        'entry_time': datetime.now(),
        'direction': 'BUY',
        'entry_price': 1987.50,
        'stop_loss': 1985.00,
        'take_profit': 1992.50,
        'lot_size': 0.1,
        'confidence': 0.85,
        'setup_quality': 8,
        'smc_steps': ['Step 1: Liquidity identified', 'Step 2: Liquidity grab confirmed'],
        'reasoning': 'Bullish OB retest with BOS confirmation',
        'session': 'NEW_YORK',
        'timeframe': 'M5'
    }
    
    success = dm.save_trade(sample_trade)
    
    # Test performance summary
    summary = dm.get_performance_summary(30)
    
    # Test system event logging
    dm.log_system_event('TEST', 'INFO', 'Data manager test completed')
    
    print("✅ Data Manager Test Results:")
    print(f"   Trade saved: {success}")
    print(f"   Performance summary: {len(summary)} metrics")
    print(f"   Database file: {dm.db_path}")
    
    # Cleanup test database
    try:
        os.remove("test_gold_digger.db")
        print("   Test database cleaned up")
    except:
        pass
    
    return True

if __name__ == "__main__":
    test_data_manager()
