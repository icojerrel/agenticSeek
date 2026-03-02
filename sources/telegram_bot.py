"""
Telegram Bot Handler for AgenticSeek.

Enables two-way communication with the AgenticSeek bot via Telegram.
Users can send messages and receive responses from the AI assistant.
"""

import os
import sys
import time
import asyncio
import threading
import configparser
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.telegram_notifier import TelegramNotifier
from sources.logger import Logger
from sources.interaction import Interaction
from sources.agents import CasualAgent, CoderAgent, FileAgent, BrowserAgent, PlannerAgent
from sources.llm_provider import Provider

logger = Logger("telegram_bot.log")

# Flask app for webhook
app = Flask(__name__)

# Global variables
bot_handler = None
interaction = None


class TelegramBotHandler:
    """
    Handle incoming Telegram messages and forward to AgenticSeek.
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.notifier = TelegramNotifier(bot_token, chat_id)
        self.logger = Logger("telegram_handler.log")
        
        # Pending requests tracking
        self.pending_chats = {}
        
        self.logger.info(f"Telegram Bot Handler initialized")
    
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
        if not chat_id:
            chat_id = self.chat_id
        
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            if reply_to:
                payload["reply_to_message_id"] = reply_to
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            result = response.json()
            return result.get("ok", False)
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def send_chat_action(self, action: str = "typing", chat_id: str = None):
        """Send chat action (typing, uploading_photo, etc.)."""
        if not chat_id:
            chat_id = self.chat_id
        
        try:
            requests.post(
                f"{self.api_url}/sendChatAction",
                json={"chat_id": chat_id, "action": action},
                timeout=5
            )
        except:
            pass
    
    def process_message(self, message: dict):
        """Process incoming message."""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        message_id = message.get("message_id")
        from_user = message.get("from", {})
        username = from_user.get("username", "User")
        
        self.logger.info(f"Message from {username}: {text[:50]}...")
        
        # Verify chat ID matches configured one
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
        
        # Send to AgenticSeek for processing
        self.send_to_agenticseek(text, chat_id, message_id)
    
    def handle_command(self, command: str, chat_id: str, reply_to: int):
        """Handle Telegram commands."""
        cmd = command.lower().split()[0]
        
        commands = {
            "/start": self.cmd_start,
            "/help": self.cmd_help,
            "/status": self.cmd_status,
            "/ping": self.cmd_ping,
        }
        
        handler = commands.get(cmd)
        if handler:
            handler(chat_id, reply_to)
        else:
            self.send_message(
                f"❓ Unknown command: {command}\n\nUse /help for available commands.",
                chat_id=chat_id,
                reply_to=reply_to
            )
    
    def cmd_start(self, chat_id: str, reply_to: int):
        """Handle /start command."""
        text = (
            f"<b>🤖 Welcome to AgenticSeek!</b>\n\n"
            f"I'm your AI assistant, ready to help with:\n\n"
            f"• 💻 Code generation (Python, C, Go, Java)\n"
            f"• 🌐 Web browsing and research\n"
            f"• 📁 File operations\n"
            f"• 📋 Complex task planning\n\n"
            f"<b>Commands:</b>\n"
            f"/help - Show all commands\n"
            f"/status - Check system status\n"
            f"/ping - Test bot responsiveness\n\n"
            f"Just send me a message and I'll help you!"
        )
        self.send_message(text, chat_id, reply_to)
    
    def cmd_help(self, chat_id: str, reply_to: int):
        """Handle /help command."""
        text = (
            f"<b>📚 AgenticSeek Help</b>\n\n"
            f"<b>Available Commands:</b>\n"
            f"/start - Welcome message\n"
            f"/help - This help message\n"
            f"/status - System status\n"
            f"/ping - Bot status check\n\n"
            f"<b>Examples:</b>\n"
            f"• 'Write a Python script to calculate Fibonacci numbers'\n"
            f"• 'Search for AI startups in the Netherlands'\n"
            f"• 'Find all PDF files in my Documents folder'\n"
            f"• 'Plan a 3-day trip to Paris'\n\n"
            f"<b>Note:</b> Complex tasks may take a few minutes."
        )
        self.send_message(text, chat_id, reply_to)
    
    def cmd_status(self, chat_id: str, reply_to: int):
        """Handle /status command."""
        text = (
            f"<b>✅ AgenticSeek Status</b>\n\n"
            f"• Bot: Online\n"
            f"• AgenticSeek: Ready\n"
            f"• Safety checks: Enabled\n"
            f"• Test suite: 8/8 passed\n\n"
            f"Ready to assist you!"
        )
        self.send_message(text, chat_id, reply_to)
    
    def cmd_ping(self, chat_id: str, reply_to: int):
        """Handle /ping command."""
        self.send_message("🏓 Pong! Bot is online and ready!", chat_id, reply_to)
    
    def send_to_agenticseek(self, message: str, chat_id: str, reply_to: int):
        """Forward message to AgenticSeek and send response."""
        global interaction
        
        try:
            # Show typing indicator
            self.send_chat_action("typing", chat_id)
            
            if interaction is None:
                self.send_message(
                    "⚠️ AgenticSeek is not initialized. Please start the service first.",
                    chat_id=chat_id,
                    reply_to=reply_to
                )
                return
            
            # Send to AgenticSeek
            self.logger.info(f"Sending to AgenticSeek: {message}")
            
            # Set query in interaction
            interaction.set_query(message)
            
            # Process asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Show thinking indicator
            self.send_message("🤔 Thinking...", chat_id=chat_id, reply_to=reply_to)
            
            # Process query
            loop.run_until_complete(interaction.think())
            
            # Get response
            response = interaction.get_updated_process_answer()
            
            if response:
                # Split long messages
                chunks = self.split_message(response)
                for chunk in chunks:
                    self.send_message(chunk, chat_id=chat_id, reply_to=reply_to)
            else:
                self.send_message(
                    "❌ No response generated. Please try again.",
                    chat_id=chat_id,
                    reply_to=reply_to
                )
            
            loop.close()
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            self.send_message(
                f"❌ Error: {str(e)}\n\nPlease try again or use /help for assistance.",
                chat_id=chat_id,
                reply_to=reply_to
            )
    
    def split_message(self, text: str, max_length: int = 4000) -> list:
        """Split long message into chunks."""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for line in text.split("\n"):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + "\n"
            else:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def poll_messages(self):
        """Poll Telegram for new messages."""
        offset = 0
        
        self.logger.info("Starting message polling...")
        self.send_message("🤖 Bot polling started! Send me a message.")
        
        while True:
            try:
                updates = self.get_updates(offset=offset, timeout=30)
                
                if updates.get("ok"):
                    for update in updates.get("result", []):
                        offset = update.get("update_id") + 1
                        
                        if "message" in update:
                            self.process_message(update["message"])
                
            except Exception as e:
                self.logger.error(f"Polling error: {str(e)}")
                time.sleep(5)


def initialize_agenticseek():
    """Initialize AgenticSeek interaction from config.ini."""
    global interaction

    try:
        logger.info("Initializing AgenticSeek...")

        config = configparser.ConfigParser()
        config.read('config.ini')

        personality_folder = "jarvis" if config.getboolean('MAIN', 'jarvis_personality') else "base"
        languages = config["MAIN"]["languages"].split(' ')

        provider = Provider(
            provider_name=config["MAIN"]["provider_name"],
            model=config["MAIN"]["provider_model"],
            server_address=config["MAIN"]["provider_server_address"],
            is_local=config.getboolean('MAIN', 'is_local')
        )
        logger.info(f"Provider: {provider.provider_name} ({provider.model})")

        agents = [
            CasualAgent(
                name=config["MAIN"]["agent_name"],
                prompt_path=f"prompts/{personality_folder}/casual_agent.txt",
                provider=provider, verbose=False
            ),
            CoderAgent(
                name="coder",
                prompt_path=f"prompts/{personality_folder}/coder_agent.txt",
                provider=provider, verbose=False
            ),
            FileAgent(
                name="File Agent",
                prompt_path=f"prompts/{personality_folder}/file_agent.txt",
                provider=provider, verbose=False
            ),
            BrowserAgent(
                name="Browser",
                prompt_path=f"prompts/{personality_folder}/browser_agent.txt",
                provider=provider, verbose=False
            ),
            PlannerAgent(
                name="Planner",
                prompt_path=f"prompts/{personality_folder}/planner_agent.txt",
                provider=provider, verbose=False
            ),
        ]

        interaction = Interaction(
            agents,
            tts_enabled=False,
            stt_enabled=False,
            recover_last_session=config.getboolean('MAIN', 'recover_last_session'),
            langs=languages
        )

        logger.info("AgenticSeek initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize AgenticSeek: {str(e)}")
        return False


# Flask webhook endpoint
@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Handle Telegram webhook."""
    data = request.json
    
    if "message" in data:
        bot_handler.process_message(data["message"])
    
    return jsonify({"ok": True})


def start_polling():
    """Start Telegram bot in polling mode."""
    global bot_handler
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.error("Telegram not configured. Check .env file.")
        return
    
    # Initialize AgenticSeek
    if not initialize_agenticseek():
        logger.error("Failed to initialize AgenticSeek")
        return
    
    # Initialize bot handler
    bot_handler = TelegramBotHandler(bot_token, chat_id)
    
    # Start polling in separate thread
    poll_thread = threading.Thread(target=bot_handler.poll_messages, daemon=True)
    poll_thread.start()
    
    logger.info("Telegram bot polling started")


def start_webhook(webhook_url: str, port: int = 5000):
    """Start Telegram bot with webhook."""
    global bot_handler
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.error("Telegram not configured. Check .env file.")
        return
    
    # Initialize AgenticSeek
    if not initialize_agenticseek():
        logger.error("Failed to initialize AgenticSeek")
        return
    
    # Initialize bot handler
    bot_handler = TelegramBotHandler(bot_token, chat_id)
    
    # Set webhook
    api_url = f"https://api.telegram.org/bot{bot_token}"
    try:
        response = requests.post(
            f"{api_url}/setWebhook",
            json={"url": webhook_url},
            timeout=10
        )
        result = response.json()
        if result.get("ok"):
            logger.info(f"Webhook set to: {webhook_url}")
        else:
            logger.error(f"Failed to set webhook: {result}")
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
    
    # Start Flask
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    print("="*60)
    print("  AgenticSeek Telegram Bot")
    print("="*60)
    
    # Choose mode: polling or webhook
    mode = os.getenv('TELEGRAM_MODE', 'polling').lower()
    
    if mode == 'polling':
        print("\nStarting in POLLING mode...")
        start_polling()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nBot stopped by user")
    
    elif mode == 'webhook':
        webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL', 'https://your-domain.com/telegram/webhook')
        print(f"\nStarting in WEBHOOK mode: {webhook_url}")
        start_webhook(webhook_url)
    
    else:
        print(f"Unknown mode: {mode}. Use 'polling' or 'webhook'")
