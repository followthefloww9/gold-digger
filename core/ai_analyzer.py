"""
Gold Digger AI Bot - AI Analyzer
Wrapper for Gemini AI analysis functionality
"""

import logging
from typing import Dict, Optional, List
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """
    AI Analyzer wrapper for Gemini client
    Provides market analysis and sentiment analysis
    """
    
    def __init__(self):
        """Initialize AI analyzer with Gemini client"""
        try:
            self.gemini_client = GeminiClient()
            self.initialized = True
            logger.info("✅ AI Analyzer initialized with Gemini client")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Analyzer: {e}")
            self.gemini_client = None
            self.initialized = False
    
    def analyze_market_sentiment(self, prompt: str) -> Optional[str]:
        """
        Analyze market sentiment using Gemini AI
        
        Args:
            prompt: Market data or analysis prompt
            
        Returns:
            AI analysis response or None if failed
        """
        if not self.initialized or not self.gemini_client:
            logger.error("❌ AI Analyzer not properly initialized")
            return None
        
        try:
            # Use Gemini client for analysis
            response = self.gemini_client.get_trading_decision(prompt)
            
            if response and 'analysis' in response:
                return response['analysis']
            elif response and 'error' not in response:
                # If response is a string, return it directly
                return str(response)
            else:
                logger.warning("⚠️ No valid analysis from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"❌ Market sentiment analysis error: {e}")
            return None
    
    def analyze_trade_signal(self, market_data: Dict, context: str = "") -> Optional[Dict]:
        """
        Analyze trade signal using Gemini AI
        
        Args:
            market_data: Market data dictionary
            context: Additional context for analysis
            
        Returns:
            Trade signal analysis or None if failed
        """
        if not self.initialized or not self.gemini_client:
            logger.error("❌ AI Analyzer not properly initialized")
            return None
        
        try:
            # Format market data for Gemini
            prompt = f"Analyze this gold market data for trading signals: {market_data}"
            if context:
                prompt += f" Context: {context}"
            
            # Get trading decision from Gemini
            response = self.gemini_client.get_trading_decision(prompt)
            
            if response and isinstance(response, dict):
                return response
            else:
                logger.warning("⚠️ No valid trade signal from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"❌ Trade signal analysis error: {e}")
            return None
    
    def get_risk_assessment(self, trade_data: Dict) -> Optional[Dict]:
        """
        Get risk assessment using Gemini AI
        
        Args:
            trade_data: Trade data for risk analysis
            
        Returns:
            Risk assessment or None if failed
        """
        if not self.initialized or not self.gemini_client:
            logger.error("❌ AI Analyzer not properly initialized")
            return None
        
        try:
            # Format trade data for risk analysis
            prompt = f"Assess the risk for this gold trade: {trade_data}"
            
            # Get risk analysis from Gemini
            response = self.gemini_client.analyze_risk(trade_data)
            
            if response and isinstance(response, dict):
                return response
            else:
                logger.warning("⚠️ No valid risk assessment from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"❌ Risk assessment error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if AI analyzer is available and working"""
        return self.initialized and self.gemini_client is not None
    
    def test_connection(self) -> Dict:
        """
        Test AI analyzer connection
        
        Returns:
            Test results dictionary
        """
        if not self.initialized:
            return {
                'success': False,
                'error': 'AI Analyzer not initialized',
                'gemini_available': False
            }
        
        try:
            # Test with simple prompt
            test_prompt = "Test connection: Analyze gold price at $3340"
            response = self.analyze_market_sentiment(test_prompt)
            
            success = response is not None and len(str(response)) > 10
            
            return {
                'success': success,
                'gemini_available': True,
                'response_length': len(str(response)) if response else 0,
                'test_response': str(response)[:100] if response else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'gemini_available': self.gemini_client is not None
            }
