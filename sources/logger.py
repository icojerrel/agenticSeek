import os, sys
from typing import List, Tuple, Type, Dict
import datetime
import logging
from logging.handlers import RotatingFileHandler

class Logger:
    """
    Enhanced Logger class with structured logging support.
    
    Features:
    - File logging with rotation (max 10MB, 5 backup files)
    - Multiple log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - Optional console output with colored formatting
    - Context-aware logging with module names
    """
    
    # ANSI color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, log_filename: str, 
                 console_output: bool = False,
                 max_bytes: int = 10*1024*1024,  # 10MB
                 backup_count: int = 5,
                 log_level: int = logging.DEBUG):
        """
        Initialize the logger.
        
        Args:
            log_filename: Name of the log file
            console_output: If True, also log to console with colors
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup log files to keep
            log_level: Minimum log level to record
        """
        self.folder = '.logs'
        self.create_folder(self.folder)
        self.log_path = os.path.join(self.folder, log_filename)
        self.enabled = True
        self.logger = None
        self.last_log_msg = ""
        self.console_output = console_output
        
        if self.enabled:
            self.create_logging(log_filename, max_bytes, backup_count, log_level)

    def create_logging(self, log_filename: str, max_bytes: int, backup_count: int, log_level: int):
        """
        Create logging configuration with file handler and optional console handler.
        """
        self.logger = logging.getLogger(log_filename)
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()
        self.logger.propagate = False
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.log_path, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Optional console handler
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def create_folder(self, path):
        """Create log dir"""
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.enabled = False
            return False

    def log(self, message, level=logging.INFO):
        """Log a message at the specified level."""
        if self.last_log_msg == message:
            return
        if self.enabled:
            self.last_log_msg = message
            self.logger.log(level, message)

    def debug(self, message: str):
        """Log a debug message."""
        self.log(message, level=logging.DEBUG)

    def info(self, message: str):
        """Log an info message."""
        self.log(message, level=logging.INFO)

    def warning(self, message: str):
        """Log a warning message."""
        self.log(message, level=logging.WARN)

    def error(self, message: str, exc_info: bool = False):
        """
        Log an error message.
        
        Args:
            message: Error message to log
            exc_info: If True, include exception traceback
        """
        if exc_info:
            self.logger.error(message, exc_info=True)
        else:
            self.log(message, level=logging.ERROR)

    def critical(self, message: str, exc_info: bool = False):
        """
        Log a critical message.
        
        Args:
            message: Critical message to log
            exc_info: If True, include exception traceback
        """
        if exc_info:
            self.logger.critical(message, exc_info=True)
        else:
            self.log(message, level=logging.CRITICAL)

    def log_context(self, context: str, message: str, level=logging.INFO):
        """
        Log a message with additional context.
        
        Args:
            context: Context identifier (e.g., function name, operation)
            message: Message to log
            level: Log level
        """
        full_message = f"[{context}] {message}"
        self.log(full_message, level)

    def get_log_stats(self) -> Dict[str, int]:
        """
        Get statistics about log file.
        
        Returns:
            Dictionary with log file statistics
        """
        if not os.path.exists(self.log_path):
            return {"exists": False}
        
        stats = {
            "exists": True,
            "size_bytes": os.path.getsize(self.log_path),
            "path": self.log_path
        }
        return stats

    def clear_logs(self):
        """Clear all log files."""
        try:
            if os.path.exists(self.log_path):
                os.remove(self.log_path)
            # Remove rotated log files
            for i in range(1, 10):
                rotated = f"{self.log_path}.{i}"
                if os.path.exists(rotated):
                    os.remove(rotated)
        except Exception as e:
            self.error(f"Failed to clear logs: {str(e)}")

if __name__ == "__main__":
    # Test the enhanced logger
    lg = Logger("test.log", console_output=True)
    lg.debug("Debug message")
    lg.info("Info message")
    lg.warning("Warning message")
    lg.error("Error message")
    lg.critical("Critical message")
    lg.log_context("test_function", "Context-aware message")
    
    print(f"Log stats: {lg.get_log_stats()}")
    

        