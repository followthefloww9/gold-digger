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
            # Convert prompt to market context format
            market_context = {
                'prompt': prompt,
                'current_price': 3340.0,  # Default price
                'analysis_request': prompt
            }

            response = self.gemini_client.get_trade_decision(market_context)

            if response and 'analysis' in response:
                return response['analysis']
            elif response and isinstance(response, dict):
                # Extract analysis from trade decision response
                analysis_parts = []
                if 'trade_decision' in response:
                    analysis_parts.append(f"Decision: {response['trade_decision']}")
                if 'reasoning' in response:
                    analysis_parts.append(f"Reasoning: {response['reasoning']}")
                if 'market_outlook' in response:
                    analysis_parts.append(f"Outlook: {response['market_outlook']}")

                return " | ".join(analysis_parts) if analysis_parts else str(response)
            elif response and 'error' not in str(response):
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
            market_context = {
                'market_data': market_data,
                'context': context,
                'current_price': market_data.get('Close', [3340.0])[-1] if isinstance(market_data, dict) else 3340.0
            }

            # Get trading decision from Gemini
            response = self.gemini_client.get_trade_decision(market_context)

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
            market_context = {
                'trade_data': trade_data,
                'risk_analysis_request': True,
                'current_price': trade_data.get('entry_price', 3340.0)
            }

            # Get risk analysis from Gemini (using trade decision method)
            response = self.gemini_client.get_trade_decision(market_context)

            if response and isinstance(response, dict):
                # Extract risk-related information
                risk_assessment = {
                    'risk_level': response.get('confidence_score', 0.5),
                    'stop_loss': response.get('stop_loss', 0),
                    'take_profit': response.get('take_profit', 0),
                    'risk_reward_ratio': response.get('risk_reward_ratio', 1.0),
                    'analysis': response.get('reasoning', 'No risk analysis available')
                }
                return risk_assessment
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
