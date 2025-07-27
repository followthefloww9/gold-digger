"""
Gold Digger AI Bot - Google Gemini 2.5 Flash Client
Handles AI-powered trade analysis and decision making
"""

import os
import json
import logging
import re
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Import the NEW Google Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini SDK not available. Install with: pip install google-generativeai")

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Google Gemini 2.5 Flash AI client for trading decisions
    Provides intelligent market analysis and trade validation
    """
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = 'gemini-2.5-flash'  # Latest Gemini 2.5 Flash model
        self.client = None
        self.model = None

        # Rate limiting settings
        self.requests_per_minute = int(os.getenv('GEMINI_REQUESTS_PER_MINUTE', '60'))
        self.min_confidence = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.6'))  # Lowered for better usability

        # Caching settings
        self.cache_enabled = True
        self.cache_duration = 300  # 5 minutes
        self.response_cache = {}

        # Error handling settings
        self.max_retries = 3
        self.retry_delay = 1  # seconds

        # Initialize client
        self._initialize_client()

        logger.info("GeminiClient initialized with caching and improved error handling")

    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if valid"""
        if not self.cache_enabled or cache_key not in self.response_cache:
            return None

        cached_data = self.response_cache[cache_key]
        cache_time = datetime.fromisoformat(cached_data['timestamp'])

        if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
            logger.info("Using cached response")
            return cached_data['response']
        else:
            # Remove expired cache
            del self.response_cache[cache_key]
            return None

    def _cache_response(self, cache_key: str, response: Dict):
        """Cache response with timestamp"""
        if self.cache_enabled:
            self.response_cache[cache_key] = {
                'response': response,
                'timestamp': datetime.now().isoformat()
            }

    def _initialize_client(self) -> bool:
        """
        Initialize the Gemini client
        
        Returns:
            True if successful, False otherwise
        """
        if not GEMINI_AVAILABLE:
            logger.error("Gemini SDK not available")
            return False
        
        if not self.api_key or self.api_key == 'your_gemini_api_key_here':
            logger.error("Gemini API key not configured")
            return False
        
        try:
            # Configure the API key (latest method from ai.google.dev)
            genai.configure(api_key=self.api_key)

            # Initialize the model with Gemini 2.5 Flash
            self.model = genai.GenerativeModel(self.model_name)

            logger.info(f"Gemini client initialized with model: {self.model_name}")
            logger.info(f"API key configured: {self.api_key[:10]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            logger.error(f"Check your API key and internet connection")
            logger.error(f"Get API key from: https://ai.google.dev/")
            return False
    
    def test_connection(self) -> Dict[str, any]:
        """
        Test Gemini API connection
        
        Returns:
            Dict with connection status and test results
        """
        if not self.model:
            return {
                'success': False,
                'error': 'Gemini client not initialized',
                'api_key_configured': bool(self.api_key and self.api_key != 'your_gemini_api_key_here')
            }
        
        try:
            # Simple test prompt following latest API docs
            test_prompt = "Respond with exactly 'GEMINI_TEST_SUCCESS' if you can read this message."

            # Generate content with proper error handling
            response = self.model.generate_content(test_prompt)

            if response and hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                success = 'GEMINI_TEST_SUCCESS' in response_text

                logger.info(f"Gemini test response: {response_text[:50]}...")

                return {
                    'success': success,
                    'model': self.model_name,
                    'response_received': True,
                    'api_key_configured': True,
                    'test_response': response_text[:100],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error("No response text received from Gemini")
                return {
                    'success': False,
                    'error': 'No response text received',
                    'api_key_configured': True,
                    'response_object': str(response) if response else 'None'
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini connection test failed: {error_msg}")

            # Provide more specific error messages
            if 'API_KEY_INVALID' in error_msg or 'invalid API key' in error_msg.lower():
                error_msg = "Invalid API key. Get a new one from https://ai.google.dev/"
            elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                error_msg = "API quota exceeded. Check your usage limits."
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                error_msg = "Network connection issue. Check your internet."

            return {
                'success': False,
                'error': error_msg,
                'api_key_configured': bool(self.api_key and self.api_key != 'your_gemini_api_key_here'),
                'model_name': self.model_name
            }
    
    def get_trade_decision(self, market_context: Dict) -> Dict[str, any]:
        """
        Get AI-powered trade decision based on market context
        
        Args:
            market_context: Dict containing market data and analysis
            
        Returns:
            Dict with trade decision and reasoning
        """
        if not self.model:
            return self._fallback_decision("Gemini client not available")
        
        try:
            # Construct the analysis prompt
            prompt = self._build_trading_prompt(market_context)

            # Check cache first
            cache_key = self._get_cache_key(prompt)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response

            # Generate response with retry logic
            decision = None
            for attempt in range(self.max_retries):
                try:
                    response = self.model.generate_content(prompt)

                    if response and response.text:
                        # Parse the response
                        decision = self._parse_trading_response(response.text)

                        # Validate decision
                        if decision['confidence_score'] < self.min_confidence:
                            decision['trade_decision'] = 'HOLD'
                            decision['reasoning'] += f" (Low confidence: {decision['confidence_score']:.2f})"

                        # Cache successful response
                        self._cache_response(cache_key, decision)
                        return decision
                    else:
                        raise ValueError("Empty response from Gemini")

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise e

            return self._fallback_decision("All retry attempts failed")

        except Exception as e:
            logger.error(f"Error getting trade decision: {str(e)}")
            return self._fallback_decision(f"Error: {str(e)}")
    
    def _build_trading_prompt(self, market_context: Dict) -> str:
        """
        Build comprehensive SMC strategy-focused trading analysis prompt

        Args:
            market_context: Market data and indicators

        Returns:
            Formatted prompt string following exact SMC strategy steps
        """
        prompt = f"""
You are an expert XAU/USD (Gold) trading analyst specializing in Smart Money Concepts (SMC).
Follow the EXACT 4-step SMC strategy to analyze this setup:

STRATEGY STEPS TO VALIDATE:
Step 1: Identify Liquidity - Look for session highs/lows where stops cluster
Step 2: Liquidity Grab - Confirm stop hunt with immediate retracement
Step 3: Structure Shift (BOS) - Validate trend change on lower timeframe
Step 4: Retest Entry - Enter on Order Block retest with 1:2 risk-reward

CURRENT MARKET DATA:
- Symbol: {market_context.get('symbol', 'XAUUSD')}
- Current Price: ${market_context.get('current_price', 'N/A')}
- Timeframe: {market_context.get('timeframe', 'M5')}
- Trading Session: {market_context.get('session', 'Unknown')}

SMC ANALYSIS RESULTS:
- Session Levels: {market_context.get('session_levels', 'Not identified')}
- Liquidity Grabs: {market_context.get('liquidity_grabs', 'None detected')}
- Break of Structure: {market_context.get('bos_analysis', 'No BOS confirmed')}
- Order Blocks: {market_context.get('order_blocks', 'None detected')}
- SMC Steps Completed: {market_context.get('smc_steps_completed', [])}

TECHNICAL CONFIRMATION:
- VWAP: ${market_context.get('vwap', 'N/A')} (institutional reference)
- EMA 21: ${market_context.get('ema_21', 'N/A')} (short-term trend)
- EMA 50: ${market_context.get('ema_50', 'N/A')} (medium-term trend)
- RSI: {market_context.get('rsi', 'N/A')} (momentum)
- ATR: {market_context.get('atr', 'N/A')} (volatility)

MARKET STRUCTURE:
- Overall Trend: {market_context.get('trend', 'Neutral')}
- Key Support: ${market_context.get('support', 'N/A')}
- Key Resistance: ${market_context.get('resistance', 'N/A')}

RISK MANAGEMENT:
- Account Balance: ${market_context.get('account_balance', 'N/A')}
- Risk per Trade: {market_context.get('risk_percentage', '1')}%
- Max Daily Loss: ${market_context.get('max_daily_loss', '500')}

TRADING SESSION CONTEXT:
- London Session: 08:00-16:00 UTC (High volatility, trend continuation)
- New York Session: 13:00-21:00 UTC (Breakouts, reversals)
- Asian Session: 22:00-08:00 UTC (Range-bound, liquidity building)

ANALYSIS REQUIREMENTS:
1. Verify ALL 4 SMC strategy steps are completed
2. Confirm Order Block quality and freshness
3. Validate risk-reward ratio is minimum 1:2
4. Consider session-specific behavior patterns
5. Ensure stop loss placement follows SMC rules (3-7 pips from OB)

DECISION CRITERIA:
- ONLY trade if all 4 SMC steps are validated
- Entry must be on Order Block retest
- Stop loss: 3-7 pips beyond Order Block
- Take profit: Target VWAP or 1:2 minimum ratio
- Confidence based on setup quality and step completion

Respond ONLY with a valid JSON object in this exact format:
{{
    "trade_decision": "BUY|SELL|HOLD",
    "confidence_score": 0.85,
    "entry_price": 1985.50,
    "stop_loss": 1980.00,
    "take_profit": 1995.00,
    "risk_reward_ratio": 2.0,
    "reasoning": "SMC strategy validation: Step 1-4 completed, bullish OB retest with BOS confirmation",
    "market_sentiment": "BULLISH|BEARISH|NEUTRAL",
    "setup_quality": "HIGH|MEDIUM|LOW",
    "smc_validation": "COMPLETE|INCOMPLETE",
    "session_bias": "BULLISH|BEARISH|NEUTRAL"
}}

CRITICAL: Only recommend BUY/SELL if ALL 4 SMC strategy steps are validated. Otherwise return HOLD.
Confidence should reflect setup quality: HIGH=0.8-0.95, MEDIUM=0.6-0.79, LOW=0.4-0.59
"""
        return prompt
    
    def _parse_trading_response(self, response_text: str) -> Dict[str, any]:
        """
        Parse Gemini response into structured trading decision
        Handles both JSON and natural language responses

        Args:
            response_text: Raw response from Gemini

        Returns:
            Parsed trading decision dict
        """
        try:
            # First try JSON parsing
            json_result = self._try_json_parse(response_text)
            if json_result:
                return self._validate_trading_decision(json_result)

            # Fall back to natural language parsing
            return self._parse_natural_language_trading(response_text)

        except Exception as e:
            logger.error(f"Error parsing trading response: {str(e)}")
            return self._fallback_decision(f"Parse error: {str(e)}")

    def _try_json_parse(self, response_text: str) -> Optional[Dict]:
        """Try to extract and parse JSON from response"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx > 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        return None

    def _parse_price_value(self, price_str: str) -> float:
        """
        Parse price string and convert to float
        Handles formats like: 2,680.50, $2680.50, 2680.50

        Args:
            price_str: Price string to parse

        Returns:
            Float value of the price
        """
        try:
            # Remove dollar signs and commas
            cleaned = price_str.replace('$', '').replace(',', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0

    def _parse_natural_language_trading(self, response_text: str) -> Dict[str, any]:
        """Parse natural language trading response using regex patterns"""
        try:
            # Initialize default values
            decision = {
                'action': 'HOLD',
                'confidence': 0.5,
                'entry_price': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'reasoning': response_text[:200] + '...' if len(response_text) > 200 else response_text
            }

            # Extract ACTION
            action_patterns = [
                r'ACTION:\s*(BUY|SELL|HOLD)',
                r'RECOMMENDATION:\s*(BUY|SELL|HOLD)',
                r'SIGNAL:\s*(BUY|SELL|HOLD)',
                r'\*\*ACTION:\*\*\s*(BUY|SELL|HOLD)'
            ]

            for pattern in action_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    decision['action'] = match.group(1).upper()
                    break

            # Extract CONFIDENCE
            confidence_patterns = [
                r'CONFIDENCE:\s*(\d+(?:\.\d+)?)',
                r'CONFIDENCE:\s*(\d+)/10',
                r'\*\*CONFIDENCE:\*\*\s*(\d+(?:\.\d+)?)'
            ]

            for pattern in confidence_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    conf_value = float(match.group(1))
                    # Normalize to 0-1 scale
                    decision['confidence'] = conf_value / 10.0 if conf_value > 1 else conf_value
                    break

            # Extract ENTRY price (improved patterns)
            entry_patterns = [
                r'ENTRY:\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',  # Handles $2,680.50
                r'ENTRY PRICE:\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'\*\*ENTRY:\*\*\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'ENTRY:\s*\$?(\d+(?:\.\d+)?)',  # Fallback for simple numbers
                r'ENTRY PRICE:\s*\$?(\d+(?:\.\d+)?)'
            ]

            for pattern in entry_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    decision['entry_price'] = self._parse_price_value(match.group(1))
                    break

            # Extract STOP LOSS (improved patterns)
            stop_patterns = [
                r'STOP:\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',  # Handles $2,645.00
                r'STOP LOSS:\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'\*\*STOP:\*\*\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'STOP:\s*\$?(\d+(?:\.\d+)?)',  # Fallback for simple numbers
                r'STOP LOSS:\s*\$?(\d+(?:\.\d+)?)'
            ]

            for pattern in stop_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    decision['stop_loss'] = self._parse_price_value(match.group(1))
                    break

            # Extract TAKE PROFIT / TARGET (improved patterns)
            target_patterns = [
                r'TARGET:\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',  # Handles $2,725.00
                r'TAKE PROFIT:\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'\*\*TARGET:\*\*\s*\$?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'TARGET:\s*\$?(\d+(?:\.\d+)?)',  # Fallback for simple numbers
                r'TAKE PROFIT:\s*\$?(\d+(?:\.\d+)?)'
            ]

            for pattern in target_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    decision['take_profit'] = self._parse_price_value(match.group(1))
                    break

            return self._validate_trading_decision(decision)

        except Exception as e:
            logger.error(f"Error parsing natural language response: {e}")
            return self._fallback_decision(f"Natural language parse error: {str(e)}")

    def _validate_trading_decision(self, decision: Dict) -> Dict[str, any]:
        """Validate and normalize trading decision"""
        # Ensure required fields exist with proper names
        normalized = {
            'trade_decision': decision.get('action', decision.get('trade_decision', 'HOLD')),
            'confidence_score': decision.get('confidence', decision.get('confidence_score', 0.5)),
            'entry_price': decision.get('entry_price', 0.0),
            'stop_loss': decision.get('stop_loss', 0.0),
            'take_profit': decision.get('take_profit', 0.0),
            'reasoning': decision.get('reasoning', 'AI analysis completed'),
            'timestamp': datetime.now().isoformat(),
            'model_used': self.model_name
        }

        # Validate confidence score
        if normalized['confidence_score'] > 1.0:
            normalized['confidence_score'] = normalized['confidence_score'] / 10.0

        return normalized
    
    def _fallback_decision(self, error_msg: str) -> Dict[str, any]:
        """
        Generate fallback decision when AI is unavailable
        
        Args:
            error_msg: Error message to include
            
        Returns:
            Safe fallback decision
        """
        return {
            'trade_decision': 'HOLD',
            'confidence_score': 0.0,
            'entry_price': 0.0,
            'stop_loss': 0.0,
            'take_profit': 0.0,
            'risk_reward_ratio': 0.0,
            'reasoning': f'AI unavailable: {error_msg}',
            'market_sentiment': 'NEUTRAL',
            'setup_quality': 'LOW',
            'timestamp': datetime.now().isoformat(),
            'model_used': 'FALLBACK',
            'error': error_msg
        }
    
    def get_market_sentiment(self, price_data: Dict) -> Dict[str, any]:
        """
        Get overall market sentiment analysis
        
        Args:
            price_data: Recent price action data
            
        Returns:
            Market sentiment analysis
        """
        if not self.model:
            return {'sentiment': 'NEUTRAL', 'confidence': 0.0, 'reasoning': 'AI unavailable'}
        
        try:
            prompt = f"""
Analyze the XAU/USD market sentiment based on recent price action:

RECENT PRICE DATA:
- Current: ${price_data.get('current', 'N/A')}
- 1H ago: ${price_data.get('1h_ago', 'N/A')}
- 4H ago: ${price_data.get('4h_ago', 'N/A')}
- Daily High: ${price_data.get('daily_high', 'N/A')}
- Daily Low: ${price_data.get('daily_low', 'N/A')}

Provide sentiment analysis in JSON format:
{{
    "sentiment": "BULLISH|BEARISH|NEUTRAL",
    "confidence": 0.75,
    "reasoning": "Brief explanation",
    "key_levels": ["level1", "level2"]
}}
"""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Parse response similar to trade decision
                return self._parse_sentiment_response(response.text)
            else:
                return {'sentiment': 'NEUTRAL', 'confidence': 0.0, 'reasoning': 'No response'}
                
        except Exception as e:
            logger.error(f"Error getting market sentiment: {str(e)}")
            return {'sentiment': 'NEUTRAL', 'confidence': 0.0, 'reasoning': f'Error: {str(e)}'}
    
    def _parse_sentiment_response(self, response_text: str) -> Dict[str, any]:
        """Parse sentiment analysis response with natural language support"""
        try:
            # Try JSON parsing first
            json_result = self._try_json_parse(response_text)
            if json_result:
                json_result['timestamp'] = datetime.now().isoformat()
                return json_result

            # Fall back to natural language parsing
            sentiment_data = {
                'sentiment': 'NEUTRAL',
                'score': 0.0,
                'confidence': 0.5,
                'summary': response_text[:100] + '...' if len(response_text) > 100 else response_text
            }

            # Extract SENTIMENT
            sentiment_patterns = [
                r'SENTIMENT:\s*(BULLISH|BEARISH|NEUTRAL)',
                r'SENTIMENT:\s*(POSITIVE|NEGATIVE|NEUTRAL)',
                r'\*\*SENTIMENT:\*\*\s*(BULLISH|BEARISH|NEUTRAL)'
            ]

            for pattern in sentiment_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    sentiment_value = match.group(1).upper()
                    # Normalize to standard values
                    if sentiment_value in ['POSITIVE', 'BULLISH']:
                        sentiment_data['sentiment'] = 'BULLISH'
                    elif sentiment_value in ['NEGATIVE', 'BEARISH']:
                        sentiment_data['sentiment'] = 'BEARISH'
                    else:
                        sentiment_data['sentiment'] = 'NEUTRAL'
                    break

            # Extract STRENGTH/SCORE
            strength_patterns = [
                r'STRENGTH:\s*(WEAK|MODERATE|STRONG)',
                r'SCORE:\s*(\d+(?:\.\d+)?)',
                r'\*\*STRENGTH:\*\*\s*(WEAK|MODERATE|STRONG)'
            ]

            for pattern in strength_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    strength_value = match.group(1).upper()
                    if strength_value == 'WEAK':
                        sentiment_data['score'] = 0.3
                        sentiment_data['confidence'] = 0.4
                    elif strength_value == 'MODERATE':
                        sentiment_data['score'] = 0.6
                        sentiment_data['confidence'] = 0.7
                    elif strength_value == 'STRONG':
                        sentiment_data['score'] = 0.9
                        sentiment_data['confidence'] = 0.9
                    else:
                        # Numeric score
                        try:
                            score = float(strength_value)
                            sentiment_data['score'] = score / 10.0 if score > 1 else score
                            sentiment_data['confidence'] = sentiment_data['score']
                        except:
                            pass
                    break

            sentiment_data['timestamp'] = datetime.now().isoformat()
            return sentiment_data

        except Exception as e:
            logger.error(f"Error parsing sentiment response: {e}")
            return {
                'sentiment': 'NEUTRAL',
                'score': 0.0,
                'confidence': 0.0,
                'summary': 'Parse error',
                'timestamp': datetime.now().isoformat()
            }

# Test function
def test_gemini_connection():
    """Test Gemini connection independently"""
    print("🤖 Testing Gemini AI Connection...")
    
    client = GeminiClient()
    result = client.test_connection()
    
    if result['success']:
        print("✅ Gemini AI Connection Test PASSED")
        print(f"   Model: {result['model']}")
        print(f"   API Key: Configured")
        print(f"   Response: {result.get('test_response', 'N/A')[:50]}...")
    else:
        print("❌ Gemini AI Connection Test FAILED")
        print(f"   Error: {result['error']}")
        print(f"   API Key Configured: {result.get('api_key_configured', False)}")
    
    return result

if __name__ == "__main__":
    test_gemini_connection()
