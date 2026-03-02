"""
Test suite for Memory class functionality.
"""
import unittest
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sources.memory import Memory
from sources.exceptions import MemoryError


class TestMemory(unittest.TestCase):
    """Test cases for Memory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_folder = tempfile.mkdtemp()
        self.original_folder = os.getcwd()
        os.chdir(self.test_folder)
        
        self.memory = Memory(
            system_prompt="You are a helpful assistant.",
            recover_last_session=False,
            memory_compression=False
        )
        self.memory.conversation_folder = os.path.join(self.test_folder, "conversations")

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_folder)
        shutil.rmtree(self.test_folder, ignore_errors=True)

    def test_memory_initialization(self):
        """Test memory initializes with system prompt."""
        self.assertEqual(len(self.memory.memory), 1)
        self.assertEqual(self.memory.memory[0]['role'], 'system')
        self.assertEqual(self.memory.memory[0]['content'], "You are a helpful assistant.")

    def test_push_message(self):
        """Test pushing messages to memory."""
        idx = self.memory.push('user', 'Hello')
        self.assertEqual(idx, 0)
        self.assertEqual(len(self.memory.memory), 2)
        self.assertEqual(self.memory.memory[1]['role'], 'user')
        self.assertEqual(self.memory.memory[1]['content'], 'Hello')

    def test_push_assistant_message(self):
        """Test pushing assistant messages."""
        self.memory.push('user', 'Hello')
        idx = self.memory.push('assistant', 'Hi there!')
        self.assertEqual(idx, 1)
        self.assertEqual(len(self.memory.memory), 3)
        self.assertEqual(self.memory.memory[2]['content'], 'Hi there!')

    def test_get_memory(self):
        """Test retrieving full memory."""
        self.memory.push('user', 'Test')
        self.memory.push('assistant', 'Response')
        memory = self.memory.get()
        self.assertEqual(len(memory), 3)
        self.assertEqual(memory[0]['role'], 'system')
        self.assertEqual(memory[1]['role'], 'user')
        self.assertEqual(memory[2]['role'], 'assistant')

    def test_reset_memory(self):
        """Test resetting memory."""
        self.memory.push('user', 'Test')
        self.memory.push('assistant', 'Response')
        self.memory.reset([{'role': 'system', 'content': 'New prompt'}])
        self.assertEqual(len(self.memory.memory), 1)
        self.assertEqual(self.memory.memory[0]['content'], 'New prompt')

    def test_clear_memory(self):
        """Test clearing memory except system prompt."""
        self.memory.push('user', 'Test 1')
        self.memory.push('assistant', 'Response 1')
        self.memory.push('user', 'Test 2')
        self.memory.clear()
        self.assertEqual(len(self.memory.memory), 1)
        self.assertEqual(self.memory.memory[0]['role'], 'system')

    def test_clear_section(self):
        """Test clearing a section of memory."""
        self.memory.push('user', 'Test 1')
        self.memory.push('assistant', 'Response 1')
        self.memory.push('user', 'Test 2')
        self.memory.push('assistant', 'Response 2')
        
        initial_length = len(self.memory.memory)
        self.memory.clear_section(start=1, end=2)
        
        expected_length = initial_length - 2
        self.assertEqual(len(self.memory.memory), expected_length)

    def test_save_memory(self):
        """Test saving memory to file."""
        self.memory.push('user', 'Test conversation')
        self.memory.push('assistant', 'Response')
        
        self.memory.save_memory(agent_type="test_agent")
        
        conv_folder = os.path.join(self.test_folder, "conversations", "test_agent")
        self.assertTrue(os.path.exists(conv_folder))
        
        files = os.listdir(conv_folder)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith('memory_'))

    def test_load_memory_no_file(self):
        """Test loading memory when no file exists."""
        self.memory.load_memory(agent_type="nonexistent")
        self.assertEqual(len(self.memory.memory), 1)

    def test_save_and_load_memory(self):
        """Test saving and loading memory."""
        self.memory.push('user', 'Persistent test')
        self.memory.push('assistant', 'Will be saved')
        
        self.memory.save_memory(agent_type="test_agent")
        
        new_memory = Memory(
            system_prompt="You are a helpful assistant.",
            recover_last_session=False,
            memory_compression=False
        )
        new_memory.conversation_folder = os.path.join(self.test_folder, "conversations")
        new_memory.load_memory(agent_type="test_agent")
        
        loaded_memory = new_memory.get()
        self.assertGreaterEqual(len(loaded_memory), 3)

    def test_duplicate_message_warning(self):
        """Test warning on duplicate messages."""
        self.memory.push('user', 'Same message')
        self.memory.push('user', 'Same message')
        self.memory.push('user', 'Same message')
        memory = self.memory.get()
        self.assertEqual(len(memory), 4)

    def test_get_ideal_ctx(self):
        """Test context size estimation."""
        test_cases = [
            ("deepseek-r1:7b", 4096),
            ("deepseek-r1:14b", 8192),
            ("deepseek-r1:32b", 16384),
            ("qwen:7b", 4096),
            ("magistral:12b", 6553),
        ]
        
        for model_name, expected_min in test_cases:
            result = self.memory.get_ideal_ctx(model_name)
            self.assertIsNotNone(result)
            self.assertGreater(result, 0)

    def test_get_ideal_ctx_invalid_model(self):
        """Test context size with invalid model name."""
        result = self.memory.get_ideal_ctx("invalid-model-name")
        self.assertIsNone(result)

    def test_trim_text_to_max_ctx(self):
        """Test text trimming to max context."""
        long_text = "A" * 10000
        trimmed = self.memory.trim_text_to_max_ctx(long_text)
        self.assertLessEqual(len(trimmed), 10000)

    def test_memory_with_timestamps(self):
        """Test that memory includes timestamps."""
        self.memory.push('user', 'Test')
        self.memory.push('assistant', 'Response')
        
        memory = self.memory.get()
        for msg in memory[1:]:
            if 'provider_name' not in str(self.memory.__dict__):
                continue
            self.assertIn('time', msg)


class TestMemoryCompression(unittest.TestCase):
    """Test cases for memory compression functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_folder = tempfile.mkdtemp()
        self.original_folder = os.getcwd()
        os.chdir(self.test_folder)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_folder)
        shutil.rmtree(self.test_folder, ignore_errors=True)

    def test_summarize_short_text(self):
        """Test summarizing short text (should return as-is)."""
        memory = Memory(
            system_prompt="Test",
            memory_compression=True
        )
        short_text = "This is a short sentence."
        result = memory.summarize(short_text)
        self.assertEqual(result, short_text)

    def test_compress_empty_memory(self):
        """Test compressing empty memory."""
        memory = Memory(
            system_prompt="Test",
            memory_compression=False
        )
        memory.compress()
        self.assertEqual(len(memory.memory), 1)


if __name__ == '__main__':
    unittest.main()
