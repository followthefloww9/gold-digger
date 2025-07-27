"""
Gold Digger AI Bot - Notification System
Discord, Telegram, and email alerts for trading events
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Comprehensive notification system for trading alerts
    Supports Discord webhooks, Telegram, and email notifications
    """
    
    def __init__(self):
        """Initialize notification manager"""
        # Discord settings
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK')
        
        # Telegram settings
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Email settings
        self.email_enabled = bool(os.getenv('EMAIL_USERNAME'))
        
        # Notification preferences
        self.enabled_channels = self._get_enabled_channels()
        
        logger.info(f"NotificationManager initialized with {len(self.enabled_channels)} channels")
    
    def _get_enabled_channels(self) -> List[str]:
        """Get list of enabled notification channels"""
        channels = []
        
        if self.discord_webhook:
            channels.append('discord')
        
        if self.telegram_token and self.telegram_chat_id:
            channels.append('telegram')
        
        if self.email_enabled:
            channels.append('email')
        
        return channels
    
    def send_trade_alert(self, trade_signal: Dict, market_data: Dict) -> bool:
        """
        Send trade alert to all enabled channels
        
        Args:
            trade_signal: Trade signal information
            market_data: Current market context
            
        Returns:
            True if at least one notification sent successfully
        """
        try:
            # Format trade alert message
            message = self._format_trade_alert(trade_signal, market_data)
            
            success_count = 0
            
            # Send to Discord
            if 'discord' in self.enabled_channels:
                if self._send_discord_alert(message, trade_signal):
                    success_count += 1
            
            # Send to Telegram
            if 'telegram' in self.enabled_channels:
                if self._send_telegram_alert(message):
                    success_count += 1
            
            # Send email
            if 'email' in self.enabled_channels:
                if self._send_email_alert(message, trade_signal):
                    success_count += 1
            
            logger.info(f"Trade alert sent to {success_count}/{len(self.enabled_channels)} channels")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending trade alert: {str(e)}")
            return False
    
    def _format_trade_alert(self, trade_signal: Dict, market_data: Dict) -> str:
        """Format trade alert message"""
        try:
            signal = trade_signal.get('signal', 'HOLD')
            confidence = trade_signal.get('confidence', 0) * 100
            entry_price = trade_signal.get('entry_price', 0)
            stop_loss = trade_signal.get('stop_loss', 0)
            take_profit = trade_signal.get('take_profit', 0)
            risk_reward = trade_signal.get('risk_reward_ratio', 0)
            setup_quality = trade_signal.get('setup_quality', 0)
            
            current_price = market_data.get('current_price', entry_price)
            session = market_data.get('session', 'Unknown')
            
            # Determine emoji based on signal
            emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
            
            message = f"""
🏆 **GOLD DIGGER AI ALERT** {emoji}

**Signal**: {signal}
**Confidence**: {confidence:.1f}%
**Setup Quality**: {setup_quality}/10

**Prices**:
• Current: ${current_price:.2f}
• Entry: ${entry_price:.2f}
• Stop Loss: ${stop_loss:.2f}
• Take Profit: ${take_profit:.2f}

**Risk Management**:
• Risk:Reward = 1:{risk_reward:.1f}
• Session: {session}

**SMC Analysis**:
{self._format_smc_reasoning(trade_signal)}

**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

⚠️ *This is an automated alert. Always verify before trading.*
"""
            return message.strip()
            
        except Exception as e:
            logger.error(f"Error formatting trade alert: {str(e)}")
            return f"Trade Alert: {signal} signal generated at {datetime.now()}"
    
    def _format_smc_reasoning(self, trade_signal: Dict) -> str:
        """Format SMC reasoning for alert"""
        try:
            analysis = trade_signal.get('analysis', {})
            smc_steps = analysis.get('smc_steps_completed', [])
            
            if smc_steps:
                return "\n".join([f"✅ {step}" for step in smc_steps])
            else:
                reasons = trade_signal.get('reasons', ['No specific reasoning provided'])
                return f"• {reasons[0]}" if reasons else "• Standard SMC setup detected"
                
        except Exception:
            return "• SMC analysis completed"
    
    def _send_discord_alert(self, message: str, trade_signal: Dict) -> bool:
        """Send alert to Discord webhook"""
        try:
            import requests
            
            # Create Discord embed
            embed = {
                "title": "🏆 Gold Digger AI Trade Alert",
                "description": message,
                "color": 0x00ff00 if trade_signal.get('signal') == 'BUY' else 0xff0000 if trade_signal.get('signal') == 'SELL' else 0x808080,
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Gold Digger AI Bot • Smart Money Concepts"
                },
                "fields": [
                    {
                        "name": "Signal",
                        "value": trade_signal.get('signal', 'HOLD'),
                        "inline": True
                    },
                    {
                        "name": "Confidence",
                        "value": f"{trade_signal.get('confidence', 0)*100:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "Entry Price",
                        "value": f"${trade_signal.get('entry_price', 0):.2f}",
                        "inline": True
                    }
                ]
            }
            
            payload = {
                "embeds": [embed],
                "username": "Gold Digger AI",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/2583/2583788.png"
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("Discord alert sent successfully")
                return True
            else:
                logger.error(f"Discord alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Discord alert error: {str(e)}")
            return False
    
    def _send_telegram_alert(self, message: str) -> bool:
        """Send alert to Telegram"""
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram alert sent successfully")
                return True
            else:
                logger.error(f"Telegram alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram alert error: {str(e)}")
            return False
    
    def _send_email_alert(self, message: str, trade_signal: Dict) -> bool:
        """Send email alert"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Email configuration
            smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
            username = os.getenv('EMAIL_USERNAME')
            password = os.getenv('EMAIL_PASSWORD')
            to_email = os.getenv('EMAIL_TO', username)
            
            if not all([username, password, to_email]):
                logger.warning("Email configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = to_email
            msg['Subject'] = f"Gold Digger AI Alert: {trade_signal.get('signal', 'HOLD')} Signal"
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.info("Email alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Email alert error: {str(e)}")
            return False
    
    def send_system_alert(self, alert_type: str, message: str, severity: str = 'INFO') -> bool:
        """
        Send system alert (errors, warnings, status updates)
        
        Args:
            alert_type: Type of alert (ERROR, WARNING, INFO, SUCCESS)
            message: Alert message
            severity: Alert severity level
            
        Returns:
            True if sent successfully
        """
        try:
            # Format system alert
            emoji_map = {
                'ERROR': '🚨',
                'WARNING': '⚠️',
                'INFO': 'ℹ️',
                'SUCCESS': '✅'
            }
            
            emoji = emoji_map.get(alert_type, 'ℹ️')
            
            system_message = f"""
{emoji} **GOLD DIGGER AI SYSTEM ALERT**

**Type**: {alert_type}
**Severity**: {severity}

**Message**: {message}

**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
            
            # Send to enabled channels (simplified for system alerts)
            success_count = 0
            
            if 'discord' in self.enabled_channels:
                if self._send_simple_discord_message(system_message):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending system alert: {str(e)}")
            return False
    
    def _send_simple_discord_message(self, message: str) -> bool:
        """Send simple Discord message"""
        try:
            import requests
            
            payload = {
                "content": message,
                "username": "Gold Digger AI System"
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            return response.status_code == 204
            
        except Exception:
            return False
    
    def test_notifications(self) -> Dict[str, bool]:
        """Test all notification channels"""
        results = {}
        
        test_message = """
🧪 **GOLD DIGGER AI TEST ALERT**

This is a test notification to verify your alert system is working correctly.

**Test Details**:
• Signal: TEST
• Time: {time}
• Status: System Check

If you received this message, your notifications are configured correctly! 🎉
""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
        
        # Test Discord
        if 'discord' in self.enabled_channels:
            results['discord'] = self._send_simple_discord_message(test_message)
        
        # Test Telegram
        if 'telegram' in self.enabled_channels:
            results['telegram'] = self._send_telegram_alert(test_message)
        
        # Test Email
        if 'email' in self.enabled_channels:
            test_signal = {'signal': 'TEST', 'confidence': 1.0}
            results['email'] = self._send_email_alert(test_message, test_signal)
        
        logger.info(f"Notification test results: {results}")
        return results

# Test function
def test_notifications():
    """Test notification system"""
    print("🔍 Testing Notification System...")
    
    # Create notification manager
    notifier = NotificationManager()
    
    print(f"   Enabled channels: {notifier.enabled_channels}")
    
    # Test notifications
    if notifier.enabled_channels:
        results = notifier.test_notifications()
        
        print("✅ Notification Test Results:")
        for channel, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {channel.title()}: {status}")
    else:
        print("⚠️ No notification channels configured")
        print("   Configure Discord webhook, Telegram bot, or email in .env file")
    
    return True

if __name__ == "__main__":
    test_notifications()
