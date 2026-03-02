"""
Custom exception classes for AgenticSeek.

This module defines specialized exceptions for better error handling
across the AgenticSeek codebase.
"""


class AgenticSeekException(Exception):
    """Base exception for all AgenticSeek errors."""
    pass


class AgentException(AgenticSeekException):
    """Exception raised for agent-related errors."""
    def __init__(self, message: str, agent_type: str = None):
        self.agent_type = agent_type
        super().__init__(f"[Agent: {agent_type}] {message}" if agent_type else message)


class ToolExecutionError(AgenticSeekException):
    """Exception raised when tool execution fails."""
    def __init__(self, tool_name: str, message: str, output: str = None):
        self.tool_name = tool_name
        self.output = output
        super().__init__(f"[Tool: {tool_name}] {message}")


class LLMProviderError(AgenticSeekException):
    """Exception raised for LLM provider connection or response errors."""
    def __init__(self, provider_name: str, message: str, original_error: Exception = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[Provider: {provider_name}] {message}")


class BrowserNavigationError(AgenticSeekException):
    """Exception raised when browser navigation fails."""
    def __init__(self, url: str, message: str):
        self.url = url
        super().__init__(f"[URL: {url}] {message}")


class MemoryError(AgenticSeekException):
    """Exception raised for memory management errors."""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"[Memory {operation}] {message}")


class RouterError(AgenticSeekException):
    """Exception raised when agent routing fails."""
    def __init__(self, message: str, query: str = None):
        self.query = query
        super().__init__(f"[Router] {message}" + (f" for query: '{query}'" if query else ""))


class ConfigurationError(AgenticSeekException):
    """Exception raised for configuration errors."""
    def __init__(self, section: str, key: str, message: str):
        self.section = section
        self.key = key
        super().__init__(f"[Config: {section}.{key}] {message}")


class SafetyCheckError(AgenticSeekException):
    """Exception raised when safety checks fail."""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        super().__init__(f"[Safety] Unsafe command detected '{command}': {reason}")
