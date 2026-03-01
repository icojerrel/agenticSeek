# CLAUDE.md — AgenticSeek Codebase Guide

This file provides essential context for AI assistants working on the AgenticSeek codebase.

---

## Project Overview

**AgenticSeek** is a fully local, privacy-first AI assistant that autonomously browses the web, writes and executes code, and plans complex tasks — entirely on the user's hardware. It is a local alternative to Manus AI.

- **Language**: Python (backend), TypeScript/React (frontend)
- **License**: GPL-3.0
- **Python requirement**: `>=3.10`
- **Package manager**: `uv` (lock file: `uv.lock`)

---

## Repository Structure

```
agenticSeek/
├── api.py                    # FastAPI backend server (main web entry point)
├── cli.py                    # CLI interface for local interactive sessions
├── config.ini                # Runtime configuration (provider, agent, browser settings)
├── requirements.txt          # Python dependencies (47 packages)
├── pyproject.toml            # Project metadata
├── setup.py                  # Package setup
├── docker-compose.yml        # Docker orchestration (Redis, SearxNG, Frontend, Backend)
├── Dockerfile.backend        # Backend container (Python 3.11-slim + Chrome + audio)
├── .env.example              # Environment variable template
├── .pre-commit-config.yaml   # Pre-commit hooks (TruffleHog secret scanning)
│
├── sources/                  # Core application source
│   ├── agents/               # Agent implementations
│   ├── tools/                # Tool implementations
│   ├── browser.py            # Selenium browser automation
│   ├── llm_provider.py       # Multi-provider LLM abstraction
│   ├── interaction.py        # User-agent interaction loop
│   ├── router.py             # Agent selection/routing
│   ├── memory.py             # Session memory persistence
│   ├── text_to_speech.py     # Kokoro TTS engine
│   ├── speech_to_text.py     # STT with wake-word detection
│   ├── schemas.py            # Pydantic models
│   ├── logger.py             # File-based logging
│   └── utility.py            # Shared helper functions
│
├── frontend/                 # React web interface
│   └── agentic-seek-front/   # React 19 application (port 3000)
│
├── llm_server/               # Self-hosted LLM server (Flask + Ollama/llama.cpp)
├── prompts/                  # System prompts for each agent
│   ├── base/                 # Default personality prompts
│   └── jarvis/               # "Jarvis" personality variant prompts
│
├── tests/                    # Test suite
├── searxng/                  # SearxNG configuration (docker-compose + settings.yml)
├── docs/                     # CONTRIBUTING.md, CODE_OF_CONDUCT.md, technical docs
├── scripts/                  # Utility scripts
└── crx/                      # Chrome extension files
```

---

## Architecture

### High-Level Flow

```
User Input (text or voice)
       ↓
   [Interaction]  ←→  [Memory]
       ↓
    [Router]   (selects agent by analyzing query)
       ↓
   [Agent]     (CasualAgent | CoderAgent | BrowserAgent | FileAgent | PlannerAgent | McpAgent)
       ↓
   [Tools]     (PyInterpreter | BashInterpreter | webSearch | fileFinder | ...)
       ↓
 [LLM Provider] (Ollama | OpenAI | Google | Deepseek | ...)
       ↓
  [Browser]    (Selenium automation, optional)
       ↓
  Output → [TTS] → User
```

### Agent System (`sources/agents/`)

| File | Agent Class | Purpose |
|------|-------------|---------|
| `agent.py` | `Agent` (base) | Abstract base: memory, tool management, execution |
| `casual_agent.py` | `CasualAgent` | General conversation |
| `code_agent.py` | `CoderAgent` | Code generation and execution |
| `browser_agent.py` | `BrowserAgent` | Web browsing and automation |
| `file_agent.py` | `FileAgent` | File system operations |
| `planner_agent.py` | `PlannerAgent` | Complex task planning and decomposition |
| `mcp_agent.py` | `McpAgent` | MCP protocol integration (under development) |

All agents inherit from `Agent` and implement `think()` and `execute()` methods.

### Tool System (`sources/tools/`)

Tools are invoked via **standardized blocks** that the LLM produces in its output:

```
<tool_name>
<content to execute>
</tool_name>
```

| File | Tool | Execution Backend |
|------|------|-------------------|
| `PyInterpreter.py` | Python execution | `subprocess` + `python3` |
| `BashInterpreter.py` | Bash execution | `subprocess` + `bash` |
| `C_Interpreter.py` | C execution | `gcc` compile + run |
| `GoInterpreter.py` | Go execution | `go run` |
| `JavaInterpreter.py` | Java execution | `javac` + `java` |
| `webSearch.py` | Web search | OpenAI-compatible API |
| `searxSearch.py` | Local web search | SearxNG HTTP API |
| `flightSearch.py` | Flight search | External API |
| `fileFinder.py` | File system search | Python `os`/`pathlib` |
| `safety.py` | Code safety validation | Static analysis |
| `mcpFinder.py` | MCP endpoint discovery | MCP protocol |
| `tools.py` | Base parsing class | Block extraction |

### LLM Provider Abstraction (`sources/llm_provider.py`)

Supports two categories of providers:

**Local (no API key needed):**
- `ollama` — Ollama local server (default, port 11434)
- `lm-studio` — LM-Studio local server (port 1234)
- `openai-compatible` — Any OpenAI-compatible local endpoint
- `server` — Self-hosted `llm_server/` Flask server

**Cloud APIs (require API key in `.env`):**
- `openai` — OpenAI GPT models
- `google` — Google Gemini models
- `deepseek` — Deepseek models
- `huggingface` — HuggingFace Inference API
- `togetherai` — TogetherAI
- `openrouter` — OpenRouter aggregator

---

## Configuration

### `config.ini` (Runtime Configuration)

```ini
[MAIN]
is_local = True              # Use local LLM (True) or cloud API (False)
provider_name = ollama       # LLM provider name
provider_model = deepseek-r1:14b  # Model to use
provider_server_address = 127.0.0.1:11434  # Provider endpoint
agent_name = Jarvis          # Display name for the AI
recover_last_session = False # Load previous session on startup
save_session = False         # Persist session to disk
speak = False                # Enable TTS output
listen = False               # Enable STT / voice input
jarvis_personality = False   # Use Jarvis personality prompts
languages = en               # Comma-separated language codes

[BROWSER]
headless_browser = True      # Run Chrome headless
stealth_mode = False         # Use undetected-chromedriver for stealth browsing
```

### `.env` (Environment Variables)

Copy `.env.example` to `.env` before running. Key variables:

```bash
SEARXNG_BASE_URL=http://searxng:8080    # SearxNG endpoint
REDIS_BASE_URL=redis://redis:6379/0     # Redis for Celery task queue
WORK_DIR=/path/to/workspace             # Agent workspace directory
OLLAMA_PORT=11434
LM_STUDIO_PORT=1234
BACKEND_PORT=7777

# Cloud API keys (only if using cloud providers)
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=
TOGETHER_API_KEY=
```

---

## API Endpoints (`api.py`)

The FastAPI backend runs on port `7777` and exposes:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/query` | Submit a user query (queued via Celery) |
| `GET` | `/screenshot` | Get latest browser screenshot |
| `GET` | `/health` | Health check |
| `GET` | `/is_active` | Check if agent is processing |
| `POST` | `/stop` | Stop current agent task |
| `GET` | `/latest_answer` | Poll for completed agent response |

Request body for `/query`:
```python
class QueryRequest(BaseModel):
    query: str
    uid: str = "local_user"
    language: str = "en"
```

Response body:
```python
class QueryResponse(BaseModel):
    answer: str
    agent: str
    status: str
    uid: str
    screenshots: List[str]
```

---

## Docker Services

Run with Docker Compose using profiles:

```bash
# Start all services (Redis + SearxNG + Frontend + Backend)
docker compose --profile full up -d

# Start without backend (run backend manually)
docker compose --profile core up -d

# Start only backend + dependencies
docker compose --profile backend up -d
```

| Service | Image | Port | Profile |
|---------|-------|------|---------|
| Redis | valkey:8-alpine | 6379 | core, full |
| SearxNG | searxng/searxng:latest | 8080 | core, full |
| Frontend | (built locally) | 3000 | core, full |
| Backend | (built locally) | 7777 | backend, full |

---

## Development Setup

### Local (Non-Docker)

```bash
# 1. Install dependencies with uv
pip install uv
uv sync

# 2. Copy and configure environment
cp .env.example .env
# Edit .env and config.ini as needed

# 3. Start infrastructure services
docker compose --profile core up -d

# 4. Run backend
python api.py
# or CLI mode:
python cli.py

# 5. Run frontend (separate terminal)
cd frontend/agentic-seek-front
npm install
npm start
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_tools_parsing.py -v
```

Test files:
- `tests/test_browser_agent_parsing.py` — Browser agent response parsing
- `tests/test_memory.py` — Session memory read/write
- `tests/test_provider.py` — LLM provider initialization
- `tests/test_searx_search.py` — SearxNG search queries
- `tests/test_tools_parsing.py` — Tool block extraction/parsing

---

## Key Conventions

### Adding a New Agent

1. Create `sources/agents/my_agent.py` inheriting from `Agent`
2. Implement `think(query)` and `execute()` methods
3. Add system prompt to `prompts/base/my_agent.txt` (and `prompts/jarvis/my_agent.txt`)
4. Register the agent in `sources/interaction.py` agent initialization
5. Add routing logic in `sources/router.py` so the router can select it

### Adding a New Tool

1. Create `sources/tools/MyTool.py` inheriting from `Tools`
2. Implement `execute(blocks, safety)` method
3. Register the tool in the relevant agent's tool list
4. Ensure the tool block name is unique and documented in the agent's system prompt

### Tool Block Format

LLMs generate tool invocations using XML-like blocks:

```
```python
# python code here
```

```bash
# bash commands here
```

```web_search
search query here
```
```

The `tools.py` base class parses these blocks from LLM output and dispatches them.

### Memory and Session Handling

- Memory is per-agent and stored in `sources/memory.py`
- Session persistence: enabled via `save_session = True` in `config.ini`
- Recovered via `recover_last_session = True`
- Memory is passed into every LLM call as conversation history

### Prompt Engineering

- All agent system prompts live in `prompts/base/` (default) or `prompts/jarvis/`
- Prompt files are plain `.txt` loaded at agent initialization
- Prompts define the agent's persona, available tools, and response format
- The `jarvis_personality` config flag switches between prompt directories

### LLM Provider Usage

Always use `llm_provider.py` abstraction — never instantiate LLM clients directly in agents or tools. The provider handles:
- Connection management and retries
- Streaming vs. non-streaming
- API key injection
- Provider-specific payload formatting

### Browser Automation

- All browser interactions go through `sources/browser.py` (Selenium-based)
- `BrowserAgent` uses the `Browser` class for page navigation, element interaction, and screenshot capture
- `stealth_mode = True` in `config.ini` enables `undetected-chromedriver`
- HTML → Markdown conversion is done before passing content to the LLM to reduce token count

### Logging

- Use `sources/logger.py` for all logging
- Logs write to `backend.log`
- Use `utility.py`'s `pretty_print()` for colored console output

---

## Security Considerations

- **Secret scanning**: `.pre-commit-config.yaml` uses TruffleHog to prevent credential commits
- **Code safety**: `sources/tools/safety.py` validates LLM-generated code before execution
- **No external calls by default**: The project is designed to run completely locally
- **API keys**: Stored only in `.env` (git-ignored), never hardcoded
- **Docker isolation**: Backend container limits filesystem access to the configured `WORK_DIR`

---

## Personas and Languages

- The agent's display name is set via `agent_name` in `config.ini`
- Language detection is handled in `sources/language.py` using `langid`
- Multi-language TTS/STT is supported; `languages` in `config.ini` controls enabled languages
- Chinese pinyin support via `pypinyin`

---

## Frontend (`frontend/agentic-seek-front/`)

- **Framework**: React 19 with TypeScript
- **Port**: 3000
- **Backend URL**: Configurable via `REACT_APP_BACKEND_URL` environment variable (default `http://localhost:7777`)
- **Key packages**: `axios` (HTTP), `react-markdown` (rendering), `react-scripts`
- **Polling**: Frontend polls `/latest_answer` and `/is_active` to display agent responses
- **Screenshots**: Displayed from `/screenshot` endpoint during browser agent sessions

---

## Self-Hosted LLM Server (`llm_server/`)

A separate Flask server that wraps local LLM backends:
- `ollama_handler.py` — Proxies to local Ollama instance
- `llamacpp_handler.py` — Runs `llama.cpp` models directly
- `generator.py` — Token streaming
- `cache.py` — Response caching

Start it independently before setting `provider_name = server` in `config.ini`.

---

## Contributing

See `docs/CONTRIBUTING.md` for full guidelines. Key principles:

1. **Privacy first** — All features must work fully locally without external services
2. **Agent-based architecture** — New capabilities belong in an agent or tool, not in `api.py`/`cli.py`
3. **Tool extensibility** — New integrations should be standalone tools in `sources/tools/`
4. **No hardcoded credentials** — Always use `.env` or `config.ini`
5. **Error handling** — Agents must handle LLM failures gracefully and provide user-friendly messages
6. **Test coverage** — Add tests in `tests/` for new agents and tools

Priority areas for contribution:
- Web browsing reliability improvements
- Multi-agent planning (task decomposition)
- New tool integrations
- MCP protocol support (`mcp_agent.py`)
- Multi-language TTS/STT
- Cross-platform compatibility (especially Windows)
