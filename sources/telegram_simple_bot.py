"""
Simple Telegram Bot for AgenticSeek - Standalone Version

This is a simple version that just echoes messages.
For full AgenticSeek integration, use the full version.
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sources.telegram_notifier import TelegramNotifier
from sources.logger import Logger

logger = Logger("telegram_simple_bot.log")


class SimpleTelegramBot:
    """
    Simple Telegram bot that responds to messages.
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.notifier = TelegramNotifier(bot_token, chat_id)
        self.logger = Logger("telegram_simple_bot.log")
        self.last_update_id = 0
        
        self.logger.info(f"Simple Telegram Bot initialized")
    
    def get_updates(self, offset: int = 0, timeout: int = 30) -> dict:
        """Get updates from Telegram."""
        try:
            response = requests.get(
                f"{self.api_url}/getUpdates",
                params={"offset": offset, "timeout": timeout},
                timeout=timeout + 5
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get updates: {str(e)}")
            return {}
    
    def send_message(self, text: str, chat_id: str = None, reply_to: int = None) -> bool:
        """Send message to Telegram."""
        return self.notifier.send_message(text, chat_id)
    
    def send_chat_action(self, action: str = "typing"):
        """Send chat action."""
        self.notifier.send_chat_action(action)
    
    def process_message(self, message: dict):
        """Process incoming message."""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        message_id = message.get("message_id")
        from_user = message.get("from", {})
        username = from_user.get("username", "User")
        
        self.logger.info(f"Message from {username}: {text[:50]}...")
        
        # Verify chat ID
        if str(chat_id) != str(self.chat_id):
            self.send_message(
                "⚠️ Sorry, this bot is only authorized for the configured chat ID.",
                chat_id=chat_id
            )
            return
        
        # Handle commands
        if text.startswith("/"):
            self.handle_command(text, chat_id, message_id)
            return
        
        # Echo response (replace with AgenticSeek integration)
        self.send_chat_action("typing")
        time.sleep(1)  # Simulate thinking
        
        response = self.generate_response(text)
        self.send_message(response, chat_id=chat_id, reply_to=message_id)
    
    def generate_response(self, text: str) -> str:
        """Generate a response to user message."""
        text_lower = text.lower()
        
        # Simple responses
        if "hello" in text_lower or "hi" in text_lower:
            return "👋 Hello! How can I help you today?"
        
        elif "how are you" in text_lower:
            return "✅ I'm doing great! Ready to assist you with any task."
        
        elif "what can you do" in text_lower or "help" in text_lower:
            return (
                "🤖 I'm AgenticSeek, your AI assistant!\n\n"
                "I can help you with:\n"
                "• 💻 Code generation\n"
                "• 🌐 Web browsing\n"
                "• 📁 File operations\n"
                "• 📋 Task planning\n\n"
                "Just ask me anything!"
            )
        
        elif "time" in text_lower:
            from datetime import datetime
            now = datetime.now()
            return f"🕐 Current time: {now.strftime('%H:%M:%S')}"
        
        elif "date" in text_lower:
            from datetime import datetime
            now = datetime.now()
            return f"📅 Today's date: {now.strftime('%Y-%m-%d')}"
        
        else:
            return (
                f"📨 I received your message: \"{text}\"\n\n"
                f"This is a simple echo bot. For full AI capabilities, "
                f"please integrate with AgenticSeek's interaction module.\n\n"
                f"Try /help for available commands."
            )
    
    def handle_command(self, command: str, chat_id: str, reply_to: int):
        """Handle Telegram commands."""
        cmd = command.lower().split()[0]
        
        if cmd == "/start":
            self.send_message(
                "🤖 <b>Welcome to AgenticSeek!</b>\n\n"
                "I'm your AI assistant. Send me a message and I'll help you!\n\n"
                "Use /help for available commands.",
                chat_id=chat_id,
                reply_to=reply_to
            )
        
        elif cmd == "/help":
            self.send_message(
                "📚 <b>AgenticSeek Help</b>\n\n"
                "<b>Commands:</b>\n"
                "/start - Welcome message\n"
                "/help - This help\n"
                "/status - System status\n"
                "/ping - Test bot\n\n"
                "<b>Just send any message</b> and I'll respond!",
                chat_id=chat_id,
                reply_to=reply_to
            )
        
        elif cmd == "/status":
            self.send_message(
                "✅ <b>AgenticSeek Status</b>\n\n"
                "• Bot: Online\n"
                "• Chat ID: Connected\n"
                "• Mode: Polling\n\n"
                "Ready to assist!",
                chat_id=chat_id,
                reply_to=reply_to
            )
        
        elif cmd == "/ping":
            self.send_message(
                "🏓 Pong! Bot is online and responsive!",
                chat_id=chat_id,
                reply_to=reply_to
            )
        
        else:
            self.send_message(
                f"❓ Unknown command: {command}\n\nUse /help for available commands.",
                chat_id=chat_id,
                reply_to=reply_to
            )
    
    def poll_messages(self):
        """Poll Telegram for new messages."""
        self.logger.info("Starting message polling...")
        self.send_message("🤖 Bot started! Send me a message or use /help")
        
        while True:
            try:
                updates = self.get_updates(offset=self.last_update_id, timeout=30)
                
                if updates.get("ok"):
                    for update in updates.get("result", []):
                        self.last_update_id = update.get("update_id") + 1
                        
                        if "message" in update:
                            self.process_message(update["message"])
                
            except Exception as e:
                self.logger.error(f"Polling error: {str(e)}")
                time.sleep(5)


def main():
    """Main entry point."""
    print("="*60)
    print("  AgenticSeek Telegram Bot - Simple Version")
    print("="*60)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ ERROR: Telegram not configured. Check .env file.")
        return
    
    print(f"\n✓ Bot token configured")
    print(f"✓ Chat ID: {chat_id}")
    
    # Create bot
    bot = SimpleTelegramBot(bot_token, chat_id)
    
    # Test connection
    print("\nTesting connection...")
    bot_info = bot.notifier.get_bot_info()
    if bot_info:
        print(f"✓ Bot username: @{bot_info.get('username')}")
    
    print("\nStarting message polling...")
    print("Press Ctrl+C to stop\n")
    
    try:
        bot.poll_messages()
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")


if __name__ == "__main__":
    main()
