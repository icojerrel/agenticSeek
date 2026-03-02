"""
Test suite for LLM Provider functionality.
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sources.llm_provider import Provider
from sources.exceptions import LLMProviderError, ConfigurationError


class TestProviderInitialization(unittest.TestCase):
    """Test cases for Provider initialization."""

    def test_provider_ollama_local(self):
        """Test Ollama provider initialization."""
        provider = Provider(
            provider_name="ollama",
            model="deepseek-r1:14b",
            server_address="127.0.0.1:11434",
            is_local=True
        )
        self.assertEqual(provider.provider_name, "ollama")
        self.assertEqual(provider.model, "deepseek-r1:14b")
        self.assertTrue(provider.is_local)

    def test_provider_lm_studio(self):
        """Test LM Studio provider initialization."""
        provider = Provider(
            provider_name="lm-studio",
            model="local-model",
            server_address="127.0.0.1:1234",
            is_local=True
        )
        self.assertEqual(provider.provider_name, "lm-studio")

    def test_provider_openai_api(self):
        """Test OpenAI provider initialization (requires API key)."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            provider = Provider(
                provider_name="openai",
                model="gpt-3.5-turbo",
                is_local=False
            )
            self.assertEqual(provider.provider_name, "openai")
            self.assertEqual(provider.api_key, 'test_key')

    def test_provider_unknown_provider(self):
        """Test initialization with unknown provider."""
        with self.assertRaises(ValueError) as context:
            Provider(
                provider_name="unknown_provider",
                model="test-model"
            )
        self.assertIn("Unknown provider", str(context.exception))

    def test_provider_api_key_missing(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                Provider(
                    provider_name="openai",
                    model="gpt-3.5-turbo",
                    is_local=False
                )


class TestProviderAvailability(unittest.TestCase):
    """Test cases for provider availability checking."""

    def test_is_ip_online_localhost(self):
        """Test localhost is always online."""
        provider = Provider("ollama", "test", is_local=True)
        self.assertTrue(provider.is_ip_online("127.0.0.1"))
        self.assertTrue(provider.is_ip_online("localhost"))

    def test_is_ip_online_empty_address(self):
        """Test empty address returns False."""
        provider = Provider("ollama", "test", is_local=True)
        self.assertFalse(provider.is_ip_online(""))

    def test_is_ip_online_invalid_url(self):
        """Test invalid URL handling."""
        provider = Provider("ollama", "test", is_local=True)
        result = provider.is_ip_online("not-a-valid-url-12345")
        self.assertFalse(result)


class TestProviderMethods(unittest.TestCase):
    """Test cases for Provider methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = Provider("ollama", "deepseek-r1:14b", is_local=True)

    def test_get_model_name(self):
        """Test getting model name."""
        self.assertEqual(self.provider.get_model_name(), "deepseek-r1:14b")

    def test_get_internal_url_docker(self):
        """Test internal URL detection for Docker."""
        with patch.dict(os.environ, {'DOCKER_INTERNAL_URL': 'http://host.docker.internal'}):
            provider = Provider("ollama", "test", is_local=True)
            self.assertIsNotNone(provider.internal_url)
            self.assertTrue(provider.in_docker)

    def test_get_internal_url_host(self):
        """Test internal URL detection for host mode."""
        with patch.dict(os.environ, {}, clear=True):
            provider = Provider("ollama", "test", is_local=True)
            self.assertEqual(provider.internal_url, "http://localhost")
            self.assertFalse(provider.in_docker)


class TestProviderRespond(unittest.TestCase):
    """Test cases for provider respond method."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = Provider("ollama", "deepseek-r1:14b", is_local=True)

    @patch('sources.llm_provider.OllamaClient')
    def test_ollama_fn_basic(self, mock_client):
        """Test Ollama function basic response."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = iter([
            {"message": {"content": "Hello"}}
        ])

        history = [{"role": "user", "content": "Hi"}]
        result = self.provider.ollama_fn(history)
        self.assertEqual(result, "Hello")

    @patch('sources.llm_provider.OllamaClient')
    def test_ollama_fn_streaming(self, mock_client):
        """Test Ollama function streaming response."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = iter([
            {"message": {"content": "Hel"}},
            {"message": {"content": "lo"}},
            {"message": {"content": " World"}}
        ])

        history = [{"role": "user", "content": "Hi"}]
        result = self.provider.ollama_fn(history)
        self.assertEqual(result, "Hello World")

    @patch('sources.llm_provider.requests.post')
    def test_server_fn_basic(self, mock_post):
        """Test server function basic response."""
        mock_post.return_value = MagicMock()
        mock_post.return_value.json.return_value = {
            "sentence": "Test response",
            "is_complete": True
        }

        provider = Provider("server", "test", "http://127.0.0.1:5000")
        history = [{"role": "user", "content": "Hi"}]
        
        with patch.object(provider, 'is_ip_online', return_value=True):
            result = provider.server_fn(history)
        
        self.assertEqual(result, "Test response")


class TestProviderEdgeCases(unittest.TestCase):
    """Test edge cases for providers."""

    def test_unsafe_providers_warning(self):
        """Test warning for unsafe providers."""
        with patch('sources.llm_provider.pretty_print') as mock_print:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}):
                Provider("openai", "gpt-3.5-turbo", is_local=False)
                mock_print.assert_called()

    def test_local_unsafe_provider_error(self):
        """Test error when using cloud provider as local."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test'}):
            provider = Provider("google", "gemini", is_local=True)
            with self.assertRaises(Exception):
                provider.google_fn([])


if __name__ == '__main__':
    unittest.main()
