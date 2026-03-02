"""
Shared pytest fixtures and configuration for AgenticSeek test suite.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, Mock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_config_file(test_dir):
    """Create a temporary config.ini file."""
    config_content = """
[MAIN]
is_local = True
provider_name = ollama
provider_model = deepseek-r1:14b
provider_server_address = 127.0.0.1:11434
agent_name = TestAgent
recover_last_session = False
save_session = False
speak = False
listen = False
jarvis_personality = False
languages = en

[BROWSER]
headless_browser = True
stealth_mode = False
"""
    config_path = os.path.join(test_dir, "config.ini")
    with open(config_path, 'w') as f:
        f.write(config_content)
    return config_path


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return """
This is a test response from the LLM.
I will help you with your request.
"""


@pytest.fixture
def mock_search_results():
    """Mock web search results."""
    return """
Title: Test Result 1
Snippet: This is a test snippet from result 1
Link: https://example.com/result1

Title: Test Result 2
Snippet: This is a test snippet from result 2
Link: https://example.com/result2

Title: Test Result 3
Snippet: This is a test snippet from result 3
Link: https://example.com/result3
"""


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
'''


@pytest.fixture
def sample_bash_commands():
    """Sample bash commands for testing."""
    return [
        "echo 'Hello from bash'",
        "pwd",
        "ls -la"
    ]


@pytest.fixture
def mock_browser_driver():
    """Mock Selenium WebDriver for browser testing."""
    driver = MagicMock()
    driver.page_source = "<html><body><p>Test content</p></body></html>"
    driver.current_url = "https://example.com"
    driver.window_handles = ["handle1"]
    return driver


@pytest.fixture
def test_memory_config():
    """Configuration for test memory instances."""
    return {
        "system_prompt": "You are a helpful test assistant.",
        "recover_last_session": False,
        "memory_compression": False,
        "model_provider": "test-model:7b"
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation history for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me with a task?"},
        {"role": "assistant", "content": "Of course! What do you need?"}
    ]


@pytest.fixture
def mock_provider():
    """Mock LLM provider for testing."""
    provider = MagicMock()
    provider.respond.return_value = "Mock response"
    provider.get_model_name.return_value = "test-model:7b"
    provider.is_local = True
    return provider


@pytest.fixture
def temp_work_dir(test_dir):
    """Create a temporary working directory for file operations."""
    work_dir = os.path.join(test_dir, "workspace")
    os.makedirs(work_dir, exist_ok=True)
    return work_dir


@pytest.fixture
def sample_file_content():
    """Sample file content for testing."""
    return {
        "test.txt": "This is a test file.",
        "test.py": "print('Hello from Python')",
        "test.json": '{"key": "value", "number": 42}',
        "test.md": "# Test Markdown\n\nThis is a test."
    }


@pytest.fixture
def setup_test_files(temp_work_dir, sample_file_content):
    """Create test files in the working directory."""
    created_files = []
    for filename, content in sample_file_content.items():
        filepath = os.path.join(temp_work_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        created_files.append(filepath)
    return created_files


@pytest.fixture
def mock_tool_response():
    """Mock tool execution response."""
    return {
        "success": True,
        "output": "Tool executed successfully",
        "feedback": "[success] Execution complete"
    }


@pytest.fixture
def agent_types():
    """List of available agent types."""
    return [
        "casual_agent",
        "coder_agent",
        "browser_agent",
        "file_agent",
        "planner_agent",
        "mcp_agent"
    ]


@pytest.fixture
def tool_types():
    """List of available tool types."""
    return [
        "PyInterpreter",
        "BashInterpreter",
        "C_Interpreter",
        "GoInterpreter",
        "JavaInterpreter",
        "webSearch",
        "searxSearch",
        "fileFinder"
    ]


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_searxng_response():
    """Mock SearxNG search response."""
    return {
        "query": "test query",
        "number_of_results": 3,
        "results": [
            {
                "title": "Test Result 1",
                "content": "Test content 1",
                "url": "https://example.com/1"
            },
            {
                "title": "Test Result 2",
                "content": "Test content 2",
                "url": "https://example.com/2"
            }
        ]
    }


@pytest.fixture
def router_test_cases():
    """Test cases for router classification."""
    return {
        "coding": [
            "Write a Python script to calculate Fibonacci numbers",
            "Debug this JavaScript code",
            "Create a bash script to monitor CPU usage"
        ],
        "web": [
            "Search the web for latest AI news",
            "Find information about quantum computing",
            "Look up restaurants near me"
        ],
        "files": [
            "Find my resume.docx file",
            "Search for all PDF files in Documents",
            "List all files in the current directory"
        ],
        "talk": [
            "Hello, how are you?",
            "Tell me a joke",
            "What's your favorite color?"
        ]
    }
