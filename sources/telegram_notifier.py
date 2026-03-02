"""
Telegram Notification Service for AgenticSeek.

This module provides Telegram notifications for:
- Task completion
- Error alerts
- Browser screenshots
- Voice messages
"""

import os
import requests
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

from sources.logger import Logger

# Load environment variables from .env
load_dotenv()


class TelegramNotifier:
    """
    Telegram notification service for AgenticSeek.
    
    Features:
    - Send text messages
    - Send photos/screenshots
    - Send voice messages
    - Error alerts
    - Task completion notifications
    """
    
    def __init__(self, 
                 bot_token: Optional[str] = None,
                 chat_id: Optional[str] = None,
                 enabled: bool = True):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram Bot API token
            chat_id: Target Chat ID
            enabled: Enable/disable notifications
        """
        self.logger = Logger("telegram.log")
        
        # Load from environment if not provided
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = enabled
        
        # Validate configuration
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram not configured: missing token or chat_id")
            self.enabled = False
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if self.enabled:
            self.logger.info(f"Telegram notifier initialized for chat: {self.chat_id}")
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return self.enabled and self.bot_token and self.chat_id
    
    def send_message(self, 
                     text: str, 
                     parse_mode: str = "HTML") -> bool:
        """
        Send a text message to the configured chat.
        
        Args:
            text: Message text (supports HTML/Markdown)
            parse_mode: "HTML" or "Markdown"
            
        Returns:
            True if message sent successfully
        """
        if not self.is_configured():
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=10
            )
            
            result = response.json()
            
            if result.get("ok"):
                self.logger.info(f"Message sent: {text[:50]}...")
                return True
            else:
                self.logger.error(f"Telegram API error: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def send_photo(self, 
                   photo_path: str, 
                   caption: Optional[str] = None) -> bool:
        """
        Send a photo/screenshot to the configured chat.
        
        Args:
            photo_path: Path to image file
            caption: Optional caption text
            
        Returns:
            True if photo sent successfully
        """
        if not self.is_configured():
            return False
        
        try:
            photo_file = Path(photo_path)
            
            if not photo_file.exists():
                self.logger.error(f"Photo not found: {photo_path}")
                return False
            
            with open(photo_file, 'rb') as photo:
                payload = {
                    "chat_id": self.chat_id,
                }
                
                if caption:
                    payload["caption"] = caption
                
                response = requests.post(
                    f"{self.api_url}/sendPhoto",
                    data=payload,
                    files={"photo": photo},
                    timeout=30
                )
            
            result = response.json()
            
            if result.get("ok"):
                self.logger.info(f"Photo sent: {photo_path}")
                return True
            else:
                self.logger.error(f"Telegram API error: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send photo: {str(e)}")
            return False
    
    def send_voice(self, 
                   voice_path: str, 
                   caption: Optional[str] = None) -> bool:
        """
        Send a voice message to the configured chat.
        
        Args:
            voice_path: Path to voice file (OGG/OPUS format)
            caption: Optional caption text
            
        Returns:
            True if voice message sent successfully
        """
        if not self.is_configured():
            return False
        
        try:
            voice_file = Path(voice_path)
            
            if not voice_file.exists():
                self.logger.error(f"Voice file not found: {voice_path}")
                return False
            
            with open(voice_file, 'rb') as voice:
                payload = {
                    "chat_id": self.chat_id,
                }
                
                if caption:
                    payload["caption"] = caption
                
                response = requests.post(
                    f"{self.api_url}/sendVoice",
                    data=payload,
                    files={"voice": voice},
                    timeout=30
                )
            
            result = response.json()
            
            if result.get("ok"):
                self.logger.info(f"Voice message sent: {voice_path}")
                return True
            else:
                self.logger.error(f"Telegram API error: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send voice message: {str(e)}")
            return False
    
    def notify_task_start(self, task: str) -> bool:
        """
        Send notification when a task starts.
        
        Args:
            task: Task description
            
        Returns:
            True if notification sent
        """
        text = (
            f"<b>🚀 Task Started</b>\n\n"
            f"<code>{task}</code>\n\n"
            f"I'll keep you updated on the progress!"
        )
        return self.send_message(text)
    
    def notify_task_complete(self, 
                             task: str, 
                             result_summary: str) -> bool:
        """
        Send notification when a task completes.
        
        Args:
            task: Task description
            result_summary: Brief summary of results
            
        Returns:
            True if notification sent
        """
        text = (
            f"<b>✅ Task Complete</b>\n\n"
            f"<b>Task:</b> <code>{task}</code>\n\n"
            f"<b>Result:</b>\n{result_summary}\n\n"
            f"Check AgenticSeek for full details."
        )
        return self.send_message(text)
    
    def notify_error(self, 
                     error_message: str, 
                     task: Optional[str] = None) -> bool:
        """
        Send error notification.
        
        Args:
            error_message: Error description
            task: Optional related task
            
        Returns:
            True if notification sent
        """
        text = f"<b>❌ Error</b>\n\n"
        
        if task:
            text += f"<b>Task:</b> <code>{task}</code>\n\n"
        
        text += f"<b>Error:</b>\n<code>{error_message}</code>"
        
        return self.send_message(text)
    
    def notify_screenshot(self, 
                          screenshot_path: str, 
                          description: str) -> bool:
        """
        Send screenshot with description.
        
        Args:
            screenshot_path: Path to screenshot file
            description: Description of what's shown
            
        Returns:
            True if notification sent
        """
        caption = f"<b>📸 Browser Screenshot</b>\n\n{description}"
        return self.send_photo(screenshot_path, caption)
    
    def get_bot_info(self) -> Optional[dict]:
        """
        Get bot information from Telegram API.
        
        Returns:
            Bot info dict or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            result = response.json()
            
            if result.get("ok"):
                return result.get("result")
            else:
                self.logger.error(f"Failed to get bot info: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting bot info: {str(e)}")
            return None


# Singleton instance for easy import
_notifier_instance: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """
    Get or create Telegram notifier singleton.
    
    Returns:
        TelegramNotifier instance
    """
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance


def notify_task_complete(task: str, result: str) -> bool:
    """
    Convenience function to notify task completion.
    
    Args:
        task: Task description
        result: Result summary
        
    Returns:
        True if notification sent
    """
    return get_notifier().notify_task_complete(task, result)


def notify_error(error: str, task: Optional[str] = None) -> bool:
    """
    Convenience function to notify error.
    
    Args:
        error: Error message
        task: Optional related task
        
    Returns:
        True if notification sent
    """
    return get_notifier().notify_error(error, task)


if __name__ == "__main__":
    # Test the notifier
    print("Testing Telegram Notifier...")
    
    notifier = TelegramNotifier()
    
    if not notifier.is_configured():
        print("❌ Telegram not configured. Check .env file.")
        exit(1)
    
    print(f"✓ Bot token configured")
    print(f"✓ Chat ID: {notifier.chat_id}")
    
    # Get bot info
    bot_info = notifier.get_bot_info()
    if bot_info:
        print(f"✓ Bot username: @{bot_info.get('username')}")
        print(f"✓ Bot name: {bot_info.get('first_name')}")
    
    # Send test message
    print("\nSending test message...")
    success = notifier.send_message(
        "<b>AgenticSeek Telegram Test</b>\n\n"
        "This is a test message from AgenticSeek v0.1.0\n\n"
        "✓ All systems operational!"
    )
    
    if success:
        print("✓ Test message sent successfully!")
    else:
        print("✗ Failed to send test message")
    
    print("\nTelegram Notifier ready for use!")
