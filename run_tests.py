"""
Comprehensive test suite for AgenticSeek improvements.
Run this to verify all enhancements work correctly.
"""
import sys
import os
sys.path.insert(0, '.')

def test_exceptions():
    """Test custom exceptions."""
    print("\n=== Testing Exceptions ===")
    from sources.exceptions import (
        AgenticSeekException, SafetyCheckError, ToolExecutionError,
        LLMProviderError, AgentException, MemoryError
    )
    
    try:
        raise SafetyCheckError("rm -rf", "Dangerous command")
    except SafetyCheckError as e:
        print(f"[OK] SafetyCheckError: {e}")
        assert "rm -rf" in str(e)
        assert "Dangerous command" in str(e)
    
    try:
        raise ToolExecutionError("PyInterpreter", "Execution failed", "Error output")
    except ToolExecutionError as e:
        print(f"[OK] ToolExecutionError: {e}")
        assert "PyInterpreter" in str(e)
    
    try:
        raise LLMProviderError("ollama", "Connection failed")
    except LLMProviderError as e:
        print(f"[OK] LLMProviderError: {e}")
        assert "ollama" in str(e)
    
    print("[OK] All exception tests passed!\n")

def test_safety():
    """Test safety checks."""
    print("=== Testing Safety Module ===")
    from sources.tools.safety import is_unsafe, is_any_unsafe
    
    # Test unsafe commands
    unsafe_cmds = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs.ext4 /dev/sda",
        "shutdown now",
        "kill -9 1234",
        "chmod 777 /etc",
        "del C:\\Windows\\System32",
        "format C:",
    ]
    
    for cmd in unsafe_cmds:
        result = is_unsafe(cmd)
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} '{cmd}' is unsafe: {result}")
        assert result, f"Command should be unsafe: {cmd}"
    
    # Test safe commands
    safe_cmds = [
        "ls -la",
        "pwd",
        "echo 'hello'",
        "cat file.txt",
        "grep 'pattern' file.txt",
        "python3 script.py",
    ]
    
    for cmd in safe_cmds:
        result = is_unsafe(cmd)
        status = "[OK]" if not result else "[FAIL]"
        print(f"{status} '{cmd}' is safe: {not result}")
        assert not result, f"Command should be safe: {cmd}"
    
    # Test is_any_unsafe
    assert is_any_unsafe(["ls", "rm -rf /", "pwd"]) == True
    assert is_any_unsafe(["ls", "pwd", "echo"]) == False
    print("[OK] All safety tests passed!\n")

def test_logging():
    """Test enhanced logging."""
    print("=== Testing Logger ===")
    from sources.logger import Logger
    import os
    
    logger = Logger("test_run.log", console_output=False)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    logger.log_context("test_function", "Context message")
    
    # Check log file exists
    assert os.path.exists(".logs/test_run.log"), "Log file should exist"
    
    # Check log stats
    stats = logger.get_log_stats()
    assert stats["exists"] == True
    assert stats["size_bytes"] > 0
    print(f"[OK] Log file created: {stats['size_bytes']} bytes")
    
    # Test log clearing
    logger.clear_logs()
    print("[OK] All logging tests passed!\n")

def test_memory():
    """Test memory with caching."""
    print("=== Testing Memory ===")
    from sources.memory import Memory
    import os
    
    # Test memory creation
    memory = Memory(
        system_prompt="Test prompt",
        recover_last_session=False,
        memory_compression=False,
        model_provider="test:7b"
    )
    
    # Test push
    idx = memory.push('user', 'Hello')
    assert idx == 0
    print("[OK] Memory push works")
    
    # Test get
    mem = memory.get()
    assert len(mem) == 2  # system + user message
    print("[OK] Memory get works")
    
    # Test context estimation
    ctx = memory.get_ideal_ctx("deepseek-r1:14b")
    assert ctx is not None
    assert ctx > 0
    print(f"[OK] Context estimation: {ctx} tokens")
    
    # Test cache path
    cache_path = memory.get_model_cache_path("test-model")
    assert cache_path is not None
    print(f"[OK] Cache path: {cache_path}")
    
    # Test clear
    memory.push('assistant', 'Hi there!')
    memory.clear()
    assert len(memory.get()) == 1  # Only system prompt
    print("[OK] Memory clear works")
    
    print("[OK] All memory tests passed!\n")

def test_tools():
    """Test tool safety integration."""
    print("=== Testing Tools with Safety ===")
    import os
    # Set a fake work dir for testing
    os.environ['WORK_DIR'] = os.path.join(os.getcwd(), 'test_workspace')
    os.makedirs(os.environ['WORK_DIR'], exist_ok=True)
    
    from sources.tools.PyInterpreter import PyInterpreter
    from sources.tools.BashInterpreter import BashInterpreter
    
    # Test Python interpreter
    py = PyInterpreter()
    # Check that safety parameter exists in execute method
    import inspect
    sig = inspect.signature(py.execute)
    assert 'safety' in sig.parameters
    print("[OK] PyInterpreter has safety parameter")
    
    # Test safe Python code
    safe_code = ['print("Hello, World!")', 'x = 42']
    # Don't execute, just check it loads
    blocks, path = py.load_exec_block('```python\nprint("test")\n```')
    assert blocks is not None
    assert len(blocks) == 1
    print("[OK] PyInterpreter block parsing works")
    
    # Test Bash interpreter
    bash = BashInterpreter()
    assert bash.safety_enabled == True
    print("[OK] BashInterpreter safety enabled")
    
    # Test unsafe bash detection
    from sources.tools.safety import is_unsafe
    assert is_unsafe("rm -rf /") == True
    assert is_unsafe("ls -la") == False
    print("[OK] Bash safety checks work")
    
    # Cleanup
    try:
        os.rmdir(os.environ['WORK_DIR'])
    except:
        pass
    
    print("[OK] All tool tests passed!\n")

def test_imports():
    """Test that all new modules can be imported."""
    print("\n=== Testing Module Imports ===")
    
    modules = [
        'sources.exceptions',
        'sources.logger',
        'sources.memory',
        'sources.tools.safety',
        'sources.tools.PyInterpreter',
        'sources.tools.BashInterpreter',
        'sources.tools.C_Interpreter',
        'sources.tools.GoInterpreter',
        'sources.tools.JavaInterpreter',
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except Exception as e:
            print(f"[FAIL] {module}: {e}")
            raise
    
    print("[OK] All modules import successfully!\n")

def test_documentation():
    """Test that documentation files exist."""
    print("\n=== Testing Documentation ===")
    
    docs = [
        'README.md',
        'CHANGELOG.md',
        'docs/API_REFERENCE.md',
        'docs/CONTRIBUTING.md',
        'docs/DEVELOPER_GUIDE.md',
    ]
    
    for doc in docs:
        exists = os.path.exists(doc)
        status = "[OK]" if exists else "[FAIL]"
        print(f"{status} {doc}: {'exists' if exists else 'MISSING'}")
        assert exists, f"Documentation missing: {doc}"
    
    print("[OK] All documentation exists!\n")

def test_config_files():
    """Test that configuration files exist."""
    print("\n=== Testing Configuration ===")
    
    configs = [
        'pytest.ini',
        '.pre-commit-config.yaml',
        '.github/workflows/ci.yml',
    ]
    
    for config in configs:
        exists = os.path.exists(config)
        status = "[OK]" if exists else "[FAIL]"
        print(f"{status} {config}: {'exists' if exists else 'MISSING'}")
        assert exists, f"Config file missing: {config}"
    
    print("[OK] All configuration files exist!\n")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  AgenticSeek - Comprehensive Test Suite")
    print("="*60)
    
    tests = [
        test_imports,
        test_exceptions,
        test_safety,
        test_logging,
        test_memory,
        test_tools,
        test_documentation,
        test_config_files,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] Test failed: {test.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"  Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n[SUCCESS] All tests passed! AgenticSeek improvements are working correctly.\n")
        return 0
    else:
        print(f"\n[WARNING] {failed} test(s) failed. Please review the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
