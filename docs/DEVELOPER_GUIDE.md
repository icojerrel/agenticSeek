# AgenticSeek Developer Quickstart Guide

🚀 Get up and running with AgenticSeek development in minutes.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [Running Tests](#running-tests)
3. [Code Quality](#code-quality)
4. [Common Tasks](#common-tasks)
5. [Troubleshooting](#troubleshooting)

---

## Quick Setup

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/Fosowl/agenticSeek.git
cd agenticSeek

# Install Python dependencies
pip install uv
uv sync

# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Install pre-commit hooks (recommended)
pip install pre-commit
pre-commit install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required for Docker mode:
# - SEARXNG_BASE_URL=http://searxng:8080
# - WORK_DIR=/path/to/your/workspace
```

### 3. Start Services

```bash
# Start Docker services (Redis, SearxNG, Frontend)
./start_services.sh full    # Linux/macOS
start start_services.cmd full  # Windows

# Verify services are running
docker compose ps
```

### 4. Run AgenticSeek

```bash
# Web interface
open http://localhost:3000

# CLI mode
uv run cli.py
```

---

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=sources --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_safety.py -v

# Run tests by keyword
pytest -k "memory" -v
```

### Test Markers

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Skip slow tests
pytest -m "not slow" -v
```

### Coverage Reports

```bash
# HTML report (open in browser)
pytest --cov=sources --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\\index.html  # Windows

# XML report (for CI/CD)
pytest --cov=sources --cov-report=xml

# Terminal summary
pytest --cov=sources --cov-report=term-missing
```

---

## Code Quality

### Pre-commit Hooks

```bash
# Install hooks (run once)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Skip hooks (not recommended)
git commit -m "WIP" --no-verify
```

### Manual Code Quality Checks

```bash
# Black formatting
black --check sources/ tests/

# Auto-format with Black
black sources/ tests/

# Flake8 linting
flake8 sources/ tests/ --max-line-length=127 --max-complexity=10

# MyPy type checking
mypy sources/ --ignore-missing-imports --no-strict-optional

# Security scan
bandit -r sources/ -f json -o bandit-report.json
```

### Fix Common Issues

```bash
# Format all Python files
black sources/ tests/

# Sort imports
pip install isort
isort sources/ tests/

# Fix Flake8 issues manually
# Common issues:
# - E501: Line too long → break into multiple lines
# - F401: Unused import → remove import
# - E302: Expected 2 blank lines → add blank lines
```

---

## Common Tasks

### Adding a New Tool

1. **Create tool file** (`sources/tools/my_tool.py`):
   ```python
   from sources.tools.tools import Tools

   class MyTool(Tools):
       def __init__(self):
           super().__init__()
           self.tag = "my_tool"
           self.name = "My Tool"
           self.description = "Description of what my tool does."

       def execute(self, blocks: list[str], safety: bool = True) -> str:
           # Implementation
           pass

       def execution_failure_check(self, output: str) -> bool:
           # Implementation
           pass

       def interpreter_feedback(self, output: str) -> str:
           # Implementation
           pass
   ```

2. **Add tests** (`tests/test_my_tool.py`):
   ```python
   import pytest
   from sources.tools.my_tool import MyTool

   def test_my_tool_basic():
       tool = MyTool()
       result = tool.execute(["test input"])
       assert result is not None
   ```

3. **Register in agent** (e.g., `sources/agents/coder_agent.py`):
   ```python
   from sources.tools.my_tool import MyTool

   self.tools["my_tool"] = MyTool()
   ```

4. **Update prompt** to mention the new tool

### Adding a New Agent

1. **Create agent file** (`sources/agents/my_agent.py`):
   ```python
   from sources.agents.agent import Agent

   class MyAgent(Agent):
       def __init__(self, name, prompt_path, provider, verbose=False, browser=None):
           super().__init__(name, prompt_path, provider, verbose, browser)
           self.tools = {}
           self.role = "my_role"
           self.type = "my_agent"

       async def process(self, prompt: str, speech_module) -> tuple[str, str]:
           # Implementation
           pass
   ```

2. **Create prompt file** (`prompts/base/my_agent.txt`)

3. **Register in router** (`sources/router.py`)

4. **Add tests** (`tests/test_my_agent.py`)

### Running in Docker

```bash
# Build from scratch
docker compose build

# Start all services
docker compose --profile full up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart a service
docker compose restart backend

# Clean up
docker compose down -v
```

### Debugging

```python
# Add debug logging
from sources.logger import Logger
logger = Logger("debug.log")

logger.debug("Variable value", extra={"value": my_var})
logger.info("Operation started")
logger.error("Error occurred", exc_info=True)
```

```bash
# Run with verbose logging
export LOG_LEVEL=DEBUG
uv run cli.py

# Inspect Docker container
docker compose exec backend bash

# Check service health
docker compose ps
docker compose logs backend
```

---

## Troubleshooting

### Test Failures

**Problem:** Tests fail with import errors
```bash
# Solution: Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

**Problem:** Async tests fail
```bash
# Solution: Ensure pytest-asyncio is installed
pip install pytest-asyncio
```

**Problem:** Coverage report is empty
```bash
# Solution: Run from project root
cd /path/to/agenticSeek
pytest --cov=sources
```

### Code Quality Issues

**Problem:** Black formatting keeps changing
```bash
# Solution: Run Black with project settings
black --line-length 127 sources/ tests/
```

**Problem:** MyPy reports missing imports
```bash
# Solution: Use ignore flag or add stubs
mypy sources/ --ignore-missing-imports
```

### Docker Issues

**Problem:** Services won't start
```bash
# Solution: Check Docker is running
docker info

# Clean up and restart
docker compose down -v
docker compose up -d
```

**Problem:** Port already in use
```bash
# Solution: Change port in docker-compose.yml or stop conflicting service
lsof -i :3000  # Find process using port 3000
```

### Memory/Cache Issues

**Problem:** Model download fails
```bash
# Solution: Clear cache and retry
python -c "from sources.memory import Memory; Memory('test').clear_cache()"
```

**Problem:** Out of disk space
```bash
# Solution: Clear model cache
du -sh ~/.cache/agenticseek/
rm -rf ~/.cache/agenticseek/models/
```

---

## Project Structure

```
agenticSeek/
├── sources/              # Core application code
│   ├── agents/          # Agent implementations
│   ├── tools/           # Tool implementations
│   ├── exceptions.py    # Custom exceptions
│   ├── logger.py        # Logging system
│   └── memory.py        # Memory management
├── tests/               # Test suite
│   ├── conftest.py     # Shared fixtures
│   ├── test_*.py       # Test files
│   └── __init__.py
├── docs/                # Documentation
│   ├── API_REFERENCE.md
│   ├── CONTRIBUTING.md
│   └── DEVELOPER_GUIDE.md
├── .github/workflows/   # CI/CD pipeline
├── pytest.ini          # Pytest configuration
├── .pre-commit-config.yaml
└── CHANGELOG.md
```

---

## Useful Commands

```bash
# Quick test run
pytest tests/test_safety.py::TestSafetyUnix -v

# Check what changed
git diff --stat
git status

# Format and lint
black sources/ tests/ && flake8 sources/ tests/

# Run security scan
bandit -r sources/ -ll

# Check dependencies
uv pip list
uv pip outdated

# Generate requirements
uv pip compile pyproject.toml -o requirements.txt
```

---

## Resources

- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[Changelog](CHANGELOG.md)** - Version history
- **[GitHub Issues](https://github.com/Fosowl/agenticSeek/issues)** - Bug tracker
- **[Discord](https://discord.gg/8hGDaME3TC)** - Community chat

---

**Need Help?** Open an issue on GitHub or ask in the Discord #dev channel.
