# AgenticSeek API Reference

Complete API documentation for AgenticSeek's public interfaces.

## Table of Contents

- [Core Classes](#core-classes)
- [Agents](#agents)
- [Tools](#tools)
- [LLM Providers](#llm-providers)
- [Memory System](#memory-system)
- [Browser Automation](#browser-automation)
- [Exceptions](#exceptions)

---

## Core Classes

### Interaction

**File:** `sources/interaction.py`

Handles user interaction and agent coordination.

#### Constructor

```python
Interaction(
    agents: List[Agent],
    tts_enabled: bool = True,
    stt_enabled: bool = True,
    recover_last_session: bool = False,
    langs: List[str] = ["en", "zh"]
)
```

**Parameters:**
- `agents`: List of initialized agent instances
- `tts_enabled`: Enable text-to-speech output
- `stt_enabled`: Enable speech-to-text input
- `recover_last_session`: Restore previous session on startup
- `langs`: List of supported languages

#### Methods

```python
async def think() -> bool
```
Process user input through router and selected agent.

**Returns:** `True` if processing succeeded, `False` otherwise

---

```python
def get_user() -> str
```
Get user input from microphone or keyboard.

**Returns:** User query string, or `None` on exit command

---

```python
def read_stdin() -> str
```
Read input from standard input.

**Returns:** User input string

---

```python
def save_session() -> None
```
Save current session memory for all agents.

---

```python
def load_last_session() -> None
```
Load memory from last session for all agents.

---

### AgentRouter

**File:** `sources/router.py`

Routes queries to appropriate agents using ML classification.

#### Constructor

```python
AgentRouter(
    agents: List[Agent],
    supported_language: List[str] = ["en", "fr", "zh"]
)
```

#### Methods

```python
def select_agent(query: str) -> Optional[Agent]
```
Select the best agent for a given query.

**Parameters:**
- `query`: User's natural language query

**Returns:** Selected agent instance or `None` if no match

**Raises:**
- `RouterError`: If routing fails

---

```python
def llm_router(text: str) -> Tuple[str, float]
```
Use LLM router model to classify text.

**Parameters:**
- `text`: Text to classify

**Returns:** Tuple of (label, confidence_score)

---

```python
def router_vote(text: str, labels: List[str]) -> str
```
Vote between LLM router and BART model.

**Parameters:**
- `text`: Input text
- `labels`: Available classification labels

**Returns:** Selected label

---

## Agents

### Agent (Base Class)

**File:** `sources/agents/agent.py`

Abstract base class for all agents.

#### Constructor

```python
Agent(
    name: str,
    prompt_path: str,
    provider: Provider,
    verbose: bool = False,
    browser: Optional[Browser] = None
)
```

#### Properties

- `get_agent_name: str` - Agent's display name
- `get_agent_type: str` - Agent type identifier
- `get_agent_role: str` - Agent role for routing
- `get_last_answer: str` - Last generated response
- `get_last_reasoning: str` - Last reasoning trace
- `get_tools: dict` - Available tools
- `get_success: bool` - Last operation success status

#### Methods

```python
async def process(prompt: str, speech_module: Speech) -> Tuple[str, str]
```
Process user prompt and generate response.

**Parameters:**
- `prompt`: User's input
- `speech_module`: Optional TTS module

**Returns:** Tuple of (answer, reasoning)

---

```python
async def llm_request() -> Tuple[str, str]
```
Send request to LLM provider.

**Returns:** Tuple of (response, reasoning)

---

```python
def execute_modules(answer: str) -> Tuple[bool, str]
```
Execute tool blocks found in LLM response.

**Parameters:**
- `answer`: LLM response containing tool blocks

**Returns:** Tuple of (success, feedback)

---

```python
def add_tool(name: str, tool: Callable) -> None
```
Add a tool to the agent's toolset.

---

### CoderAgent

**File:** `sources/agents/code_agent.py`

Handles code generation and execution tasks.

**Tools:**
- `PyInterpreter` - Python execution
- `BashInterpreter` - Bash commands
- `C_Interpreter` - C compilation/execution
- `GoInterpreter` - Go compilation/execution
- `JavaInterpreter` - Java compilation/execution
- `safety` - Code safety validation

---

### BrowserAgent

**File:** `sources/agents/browser_agent.py`

Handles autonomous web browsing and information gathering.

**Tools:**
- `searxSearch` - Local web search via SearxNG
- `webSearch` - External web search API

**Properties:**
- `current_page: str` - Current URL
- `search_history: List[str]` - Visited URLs
- `notes: List[str]` - Extracted information

---

### FileAgent

**File:** `sources/agents/file_agent.py`

Handles file system operations.

**Tools:**
- `fileFinder` - File search and management

---

### CasualAgent

**File:** `sources/agents/casual_agent.py`

Handles general conversation.

**Tools:** None (conversation only)

---

### PlannerAgent

**File:** `sources/agents/planner_agent.py`

Handles complex task decomposition and planning.

---

## Tools

### Tools (Base Class)

**File:** `sources/tools/tools.py`

Abstract base class for all tools.

#### Methods

```python
@abstractmethod
def execute(blocks: List[str], safety: bool) -> str
```
Execute tool functionality.

**Parameters:**
- `blocks`: Code/query blocks to execute
- `safety`: Enable safety checks

**Returns:** Execution output

---

```python
@abstractmethod
def execution_failure_check(output: str) -> bool
```
Check if execution failed.

**Parameters:**
- `output`: Tool execution output

**Returns:** `True` if failed, `False` if successful

---

```python
@abstractmethod
def interpreter_feedback(output: str) -> str
```
Generate feedback for LLM.

**Parameters:**
- `output`: Tool execution output

**Returns:** Feedback message

---

```python
def load_exec_block(llm_text: str) -> Tuple[Optional[List[str]], Optional[str]]
```
Extract code blocks from LLM response.

**Parameters:**
- `llm_text`: Raw LLM response

**Returns:** Tuple of (blocks, save_path)

---

### PyInterpreter

**File:** `sources/tools/PyInterpreter.py`

Executes Python code safely.

```python
def execute(codes: List[str], safety: bool = True) -> str
```

**Safety Checks:**
- Detects unsafe system commands
- Sandboxed execution environment
- Catches SystemExit exceptions

---

### BashInterpreter

**File:** `sources/tools/BashInterpreter.py`

Executes bash commands with safety validation.

```python
def execute(commands: List[str], safety: bool = True, timeout: int = 300) -> str
```

**Safety Checks:**
- Blocks dangerous commands (rm, dd, mkfs, etc.)
- Timeout protection
- Working directory isolation

---

### searxSearch

**File:** `sources/tools/searxSearch.py`

Performs web searches via SearxNG.

```python
def execute(queries: List[str], safety: bool = False) -> str
```

**Returns:** Formatted search results

---

### fileFinder

**File:** `sources/tools/fileFinder.py`

File system search and operations.

```python
def execute(operations: List[str], safety: bool = True) -> str
```

---

## LLM Providers

### Provider

**File:** `sources/llm_provider.py`

Unified interface for multiple LLM providers.

#### Constructor

```python
Provider(
    provider_name: str,
    model: str,
    server_address: str = "127.0.0.1:5000",
    is_local: bool = False
)
```

**Parameters:**
- `provider_name`: Provider identifier (e.g., "ollama", "openai")
- `model`: Model name to use
- `server_address`: Provider endpoint address
- `is_local`: Whether provider runs locally

**Raises:**
- `ValueError`: If provider_name is unknown
- `SystemExit`: If API key is missing for cloud providers

#### Methods

```python
def respond(history: List[dict], verbose: bool = True) -> str
```
Generate response from LLM.

**Parameters:**
- `history`: Conversation history (list of message dicts)
- `verbose`: Print response as generated

**Returns:** Generated text

**Raises:**
- `LLMProviderError`: If provider fails
- `ConnectionError`: If provider is unreachable

---

```python
def is_ip_online(address: str, timeout: int = 10) -> bool
```
Check if provider address is reachable.

---

### Supported Providers

**Local Providers:**
- `ollama` - Ollama local server
- `lm-studio` - LM Studio local server
- `openai` - Local OpenAI-compatible server

**Cloud Providers:**
- `openai` - OpenAI GPT models
- `google` - Google Gemini
- `deepseek` - DeepSeek API
- `together` - TogetherAI
- `openrouter` - OpenRouter
- `huggingface` - HuggingFace Inference API

---

## Memory System

### Memory

**File:** `sources/memory.py`

Manages conversation history and compression.

#### Constructor

```python
Memory(
    system_prompt: str,
    recover_last_session: bool = False,
    memory_compression: bool = True,
    model_provider: str = "deepseek-r1:14b"
)
```

**Parameters:**
- `system_prompt`: System prompt for conversation
- `recover_last_session`: Load previous session
- `memory_compression`: Enable automatic compression
- `model_provider`: Provider for context estimation

#### Methods

```python
def push(role: str, content: str) -> int
```
Add message to memory.

**Parameters:**
- `role`: Message role ('user', 'assistant', 'system')
- `content`: Message content

**Returns:** Index of pushed message

---

```python
def get() -> List[dict]
```
Get full conversation history.

**Returns:** List of message dictionaries

---

```python
def compress() -> None
```
Compress long messages using summarization.

---

```python
def save_memory(agent_type: str) -> None
```
Save memory to disk.

---

```python
def load_memory(agent_type: str) -> None
```
Load memory from disk.

---

```python
def clear() -> None
```
Clear all memory except system prompt.

---

```python
def clear_cache() -> None
```
Clear model cache to free disk space.

---

## Browser Automation

### Browser

**File:** `sources/browser.py`

Selenium-based browser automation with stealth features.

#### Constructor

```python
Browser(
    driver: webdriver.Chrome,
    anticaptcha_manual_install: bool = False
)
```

#### Methods

```python
def go_to(url: str) -> bool
```
Navigate to URL.

**Returns:** `True` if navigation succeeded

---

```python
def get_text() -> Optional[str]
```
Get page content as Markdown.

**Returns:** Formatted page text

---

```python
def get_navigable() -> List[str]
```
Get all valid links on page.

---

```python
def click_element(xpath: str) -> bool
```
Click element by XPath.

---

```python
def fill_form(inputs: List[str]) -> bool
```
Fill form fields.

**Parameters:**
- `inputs`: List of [field_name](value) strings

---

```python
def screenshot() -> str
```
Take page screenshot.

**Returns:** Screenshot file path

---

## Exceptions

### Exception Hierarchy

```
AgenticSeekException (base)
├── AgentException
├── ToolExecutionError
├── LLMProviderError
├── BrowserNavigationError
├── MemoryError
├── RouterError
├── ConfigurationError
└── SafetyCheckError
```

### AgenticSeekException

**File:** `sources/exceptions.py`

Base exception for all AgenticSeek errors.

---

### AgentException

Raised for agent-related errors.

```python
AgentException(message: str, agent_type: str = None)
```

---

### ToolExecutionError

Raised when tool execution fails.

```python
ToolExecutionError(tool_name: str, message: str, output: str = None)
```

---

### LLMProviderError

Raised for LLM provider connection or response errors.

```python
LLMProviderError(provider_name: str, message: str, original_error: Exception = None)
```

---

### BrowserNavigationError

Raised when browser navigation fails.

```python
BrowserNavigationError(url: str, message: str)
```

---

### SafetyCheckError

Raised when safety checks fail.

```python
SafetyCheckError(command: str, reason: str)
```

---

## Configuration

### config.ini Structure

```ini
[MAIN]
is_local = True                    # Use local LLM provider
provider_name = ollama             # Provider identifier
provider_model = deepseek-r1:14b   # Model name
provider_server_address = 127.0.0.1:11434
agent_name = Jarvis                # AI display name
recover_last_session = False       # Load previous session
save_session = False               # Save current session
speak = False                      # Enable TTS
listen = False                     # Enable STT
jarvis_personality = False         # Use Jarvis prompts
languages = en                     # Supported languages

[BROWSER]
headless_browser = True            # Run browser headless
stealth_mode = False               # Use undetected Chrome
```

---

## Examples

### Basic Usage

```python
from sources.interaction import Interaction
from sources.agents.casual_agent import CasualAgent
from sources.agents.code_agent import CoderAgent
from sources.llm_provider import Provider

# Initialize provider
provider = Provider(
    provider_name="ollama",
    model="deepseek-r1:14b",
    is_local=True
)

# Initialize agents
casual = CasualAgent(
    name="Friday",
    prompt_path="prompts/base/casual_agent.txt",
    provider=provider
)

coder = CoderAgent(
    name="CodeMaster",
    prompt_path="prompts/base/coder_agent.txt",
    provider=provider
)

# Initialize interaction
interaction = Interaction(
    agents=[casual, coder],
    tts_enabled=False,
    stt_enabled=False
)

# Process query
query = interaction.get_user()
await interaction.think()
response = interaction.get_updated_process_answer()
```

---

### Tool Usage

```python
from sources.tools.PyInterpreter import PyInterpreter

tool = PyInterpreter()
codes = ['print("Hello, World!")']
result = tool.execute(codes, safety=True)
print(result)
```

---

### Memory Management

```python
from sources.memory import Memory

memory = Memory(
    system_prompt="You are a helpful assistant.",
    memory_compression=True
)

memory.push('user', 'Hello')
memory.push('assistant', 'Hi there!')

# Get conversation
history = memory.get()

# Save session
memory.save_memory(agent_type="casual_agent")

# Clear cache
memory.clear_cache()
```

---

### Browser Automation

```python
from sources.browser import create_driver, Browser

# Create driver
driver = create_driver(headless=True, stealth_mode=True)
browser = Browser(driver)

# Navigate
browser.go_to("https://example.com")

# Get content
content = browser.get_text()
print(content)

# Take screenshot
screenshot_path = browser.screenshot()
```

---

## Version Information

**Current Version:** 0.1.0  
**Python Requirement:** >=3.10  
**License:** GPL-3.0

For more information, see [README.md](../README.md) and [CONTRIBUTING.md](../docs/CONTRIBUTING.md).
