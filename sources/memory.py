import time
import datetime
import uuid
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Type, Dict, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import configparser

from sources.utility import timer_decorator, pretty_print, animate_thinking
from sources.logger import Logger

config = configparser.ConfigParser()
config.read('config.ini')

class Memory():
    """
    Memory is a class for managing the conversation memory
    It provides a method to compress the memory using summarization model.
    
    Features:
    - Conversation history management
    - Memory compression via summarization
    - Model caching for faster startup
    - Session save/load functionality
    """
    # Cache directory for downloaded models
    MODEL_CACHE_DIR = Path.home() / ".cache" / "agenticseek" / "models"
    
    def __init__(self, system_prompt: str,
                 recover_last_session: bool = False,
                 memory_compression: bool = True,
                 model_provider: str = "deepseek-r1:14b"):
        self.memory = [{'role': 'system', 'content': system_prompt}]

        self.logger = Logger("memory.log")
        self.session_time = datetime.datetime.now()
        self.session_id = str(uuid.uuid4())
        self.conversation_folder = f"conversations/"
        self.session_recovered = False
        if recover_last_session:
            self.load_memory()
            self.session_recovered = True
        # memory compression system
        self.model = None
        self.tokenizer = None
        self.device = self.get_cuda_device()
        self.memory_compression = memory_compression
        self.model_provider = model_provider
        self.model_cache_path = None
        
        if self.memory_compression:
            self.download_model()

    def get_ideal_ctx(self, model_name: str) -> int | None:
        """
        Estimate context size based on the model name.
        EXPERIMENTAL for memory compression
        
        Args:
            model_name: Name of the model (e.g., "deepseek-r1:14b")
            
        Returns:
            Estimated context size in tokens, or None if model not recognized
        """
        import re
        import math

        def extract_number_before_b(sentence: str) -> int:
            match = re.search(r'(\d+)b', sentence, re.IGNORECASE)
            return int(match.group(1)) if match else None

        model_size = extract_number_before_b(model_name)
        if not model_size:
            return None
        base_size = 7  # Base model size in billions
        base_context = 4096  # Base context size in tokens
        scaling_factor = 1.5  # Approximate scaling factor for context size growth
        context_size = int(base_context * (model_size / base_size) ** scaling_factor)
        context_size = 2 ** round(math.log2(context_size))
        self.logger.info(f"Estimated context size for {model_name}: {context_size} tokens.")
        return context_size

    def get_model_cache_path(self, model_name: str) -> Path:
        """
        Get the cache path for a specific model.
        
        Args:
            model_name: Name of the model to cache
            
        Returns:
            Path to the model cache directory
        """
        # Create a safe directory name from model name
        safe_name = hashlib.md5(model_name.encode()).hexdigest()[:16]
        return self.MODEL_CACHE_DIR / safe_name

    def is_model_cached(self, model_name: str) -> bool:
        """
        Check if a model is already cached.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if model is cached, False otherwise
        """
        cache_path = self.get_model_cache_path(model_name)
        return cache_path.exists() and (cache_path / "config.json").exists()

    def download_model(self):
        """
        Download the memory compression model with caching.
        
        The model is cached in ~/.cache/agenticseek/models/ to avoid
        re-downloading on subsequent runs.
        """
        model_name = "pszemraj/led-base-book-summary"
        
        # Check if model is already cached
        if self.is_model_cached(model_name):
            cache_path = self.get_model_cache_path(model_name)
            animate_thinking(f"Loading cached memory compression model from {cache_path}...", color="status")
            self.logger.info(f"Loading cached model from {cache_path}")
        else:
            animate_thinking("Downloading memory compression model...", color="status")
            self.logger.info(f"Downloading model: {model_name}")
            cache_path = None
        
        try:
            # Load tokenizer and model with cache support
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.MODEL_CACHE_DIR) if cache_path is None else str(cache_path)
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=str(self.MODEL_CACHE_DIR) if cache_path is None else str(cache_path)
            )
            self.model.to(self.device)
            self.logger.info(f"Memory compression system initialized. Cache: {self.get_model_cache_path(model_name)}")
            pretty_print("Memory compression model loaded successfully", color="success")
            
        except Exception as e:
            self.logger.warning(f"Failed to load memory compression model: {str(e)}")
            pretty_print("Warning: Memory compression model failed to load. Continuing without compression.", color="warning")
            self.model = None
            self.tokenizer = None

    def get_filename(self) -> str:
        """Get the filename for the save file."""
        return f"memory_{self.session_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"

    def save_memory(self, agent_type: str = "casual_agent") -> None:
        """Save the session memory to a file."""
        if not os.path.exists(self.conversation_folder):
            self.logger.info(f"Created folder {self.conversation_folder}.")
            os.makedirs(self.conversation_folder)
        save_path = os.path.join(self.conversation_folder, agent_type)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        filename = self.get_filename()
        path = os.path.join(save_path, filename)
        json_memory = json.dumps(self.memory)
        with open(path, 'w') as f:
            self.logger.info(f"Saved memory json at {path}")
            f.write(json_memory)

    def find_last_session_path(self, path) -> str:
        """Find the last session path."""
        saved_sessions = []
        for filename in os.listdir(path):
            if filename.startswith('memory_'):
                date = filename.split('_')[1]
                saved_sessions.append((filename, date))
        saved_sessions.sort(key=lambda x: x[1], reverse=True)
        if len(saved_sessions) > 0:
            self.logger.info(f"Last session found at {saved_sessions[0][0]}")
            return saved_sessions[0][0]
        return None

    def save_json_file(self, path: str, json_memory: dict) -> None:
        """Save a JSON file."""
        try:
            with open(path, 'w') as f:
                json.dump(json_memory, f)
                self.logger.info(f"Saved memory json at {path}")
        except Exception as e:
            self.logger.warning(f"Error saving file {path}: {e}")

    def load_json_file(self, path: str) -> dict:
        """Load a JSON file."""
        json_memory = {}
        try:
            with open(path, 'r') as f:
                json_memory = json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"File not found: {path}")
            return {}
        except json.JSONDecodeError:
            self.logger.warning(f"Error decoding JSON from file: {path}")
            return {}
        except Exception as e:
            self.logger.warning(f"Error loading file {path}: {e}")
            return {}
        return json_memory

    def load_memory(self, agent_type: str = "casual_agent") -> None:
        """Load the memory from the last session."""
        if self.session_recovered == True:
            return
        pretty_print(f"Loading {agent_type} past memories... ", color="status")
        save_path = os.path.join(self.conversation_folder, agent_type)
        if not os.path.exists(save_path):
            pretty_print("No memory to load.", color="success")
            return
        filename = self.find_last_session_path(save_path)
        if filename is None:
            pretty_print("Last session memory not found.", color="warning")
            return
        path = os.path.join(save_path, filename)
        self.memory = self.load_json_file(path)
        if self.memory[-1]['role'] == 'user':
            self.memory.pop()
        self.compress()
        pretty_print("Session recovered successfully", color="success")

    def reset(self, memory: list = []) -> None:
        self.logger.info("Memory reset performed.")
        self.memory = memory

    def push(self, role: str, content: str) -> int:
        """
        Push a message to the memory.
        
        Args:
            role: Role of the message sender ('user', 'assistant', 'system')
            content: Content of the message
            
        Returns:
            Index of the pushed message
        """
        ideal_ctx = self.get_ideal_ctx(self.model_provider)
        if ideal_ctx is not None:
            if self.memory_compression and len(content) > ideal_ctx * 1.5:
                self.logger.info(f"Compressing memory: Content {len(content)} > {ideal_ctx} model context.")
                self.compress()
        curr_idx = len(self.memory)
        if self.memory[curr_idx-1]['content'] == content:
            pretty_print("Warning: same message have been pushed twice to memory", color="error")
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if config["MAIN"]["provider_name"] == "openrouter":
            self.memory.append({'role': role, 'content': content})
        else:
            self.memory.append({'role': role, 'content': content, 'time': time_str, 'model_used': self.model_provider})
        return curr_idx-1

    def clear(self) -> None:
        """Clear all memory except system prompt"""
        self.logger.info("Memory clear performed.")
        self.memory = self.memory[:1]

    def clear_section(self, start: int, end: int) -> None:
        """
        Clear a section of the memory. Ignore system message index.
        Args:
            start (int): Starting bound of the section to clear.
            end (int): Ending bound of the section to clear.
        """
        self.logger.info(f"Clearing memory section {start} to {end}.")
        start = max(0, start) + 1
        end = min(end, len(self.memory)-1) + 2
        self.memory = self.memory[:start] + self.memory[end:]

    def get(self) -> list:
        return self.memory

    def get_cuda_device(self) -> str:
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"

    def summarize(self, text: str, min_length: int = 64) -> str:
        """
        Summarize the text using the AI model.
        
        Args:
            text (str): The text to summarize
            min_length (int, optional): The minimum length of the summary. Defaults to 64.
            
        Returns:
            str: The summarized text
        """
        if self.tokenizer is None or self.model is None:
            self.logger.warning("No tokenizer or model to perform summarization.")
            return text
        if len(text) < min_length*1.5:
            return text
            
        max_length = len(text) // 2 if len(text) > min_length*2 else min_length*2
        input_text = "summarize: " + text
        
        try:
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    max_length=max_length,
                    min_length=min_length,
                    length_penalty=1.0,
                    num_beams=4,
                    early_stopping=True
                )
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summary = summary.replace('summary:', '')
            self.logger.info(f"Memory summarized from len {len(text)} to {len(summary)}.")
            self.logger.info(f"Summarized text:\n{summary}")
            return summary
        except Exception as e:
            self.logger.error(f"Summarization failed: {str(e)}")
            return text  # Return original text if summarization fails

    def compress(self) -> str:
        """
        Compress (summarize) the memory using the model.
        """
        if self.tokenizer is None or self.model is None:
            self.logger.warning("No tokenizer or model to perform memory compression.")
            return
        for i in range(len(self.memory)):
            if self.memory[i]['role'] == 'system':
                continue
            if len(self.memory[i]['content']) > 1024:
                self.memory[i]['content'] = self.summarize(self.memory[i]['content'])

    def trim_text_to_max_ctx(self, text: str) -> str:
        """
        Truncate a text to fit within the maximum context size of the model.
        
        Args:
            text: Text to truncate
            
        Returns:
            Truncated text
        """
        ideal_ctx = self.get_ideal_ctx(self.model_provider)
        return text[:ideal_ctx] if ideal_ctx is not None else text

    def compress_text_to_max_ctx(self, text) -> str:
        """
        Compress a text to fit within the maximum context size of the model.
        
        Args:
            text: Text to compress
            
        Returns:
            Compressed text
        """
        if self.tokenizer is None or self.model is None:
            self.logger.warning("No tokenizer or model to perform memory compression.")
            return text
        ideal_ctx = self.get_ideal_ctx(self.model_provider)
        if ideal_ctx is None:
            self.logger.warning("No ideal context size found.")
            return text
        while len(text) > ideal_ctx:
            self.logger.info(f"Compressing text: {len(text)} > {ideal_ctx} model context.")
            text = self.summarize(text)
        return text

    def clear_cache(self) -> None:
        """
        Clear the model cache to free up disk space.
        """
        import shutil
        if self.MODEL_CACHE_DIR.exists():
            try:
                shutil.rmtree(self.MODEL_CACHE_DIR)
                self.logger.info(f"Cleared model cache at {self.MODEL_CACHE_DIR}")
                pretty_print(f"Model cache cleared: {self.MODEL_CACHE_DIR}", color="success")
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {str(e)}")
                pretty_print(f"Failed to clear cache: {str(e)}", color="failure")

    def get_cache_size(self) -> int:
        """
        Get the total size of the model cache in bytes.
        
        Returns:
            Cache size in bytes
        """
        if not self.MODEL_CACHE_DIR.exists():
            return 0
        
        total_size = 0
        for path in self.MODEL_CACHE_DIR.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        return total_size

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    memory = Memory("You are a helpful assistant.",
                    recover_last_session=False, memory_compression=True)

    memory.push('user', "hello")
    memory.push('assistant', "how can i help you?")
    memory.push('user', "why do i get this cuda error?")
    sample_text = """
The error you're encountering:
cuda.cu:52:10: fatal error: helper_functions.h: No such file or directory
 #include <helper_functions.h>
indicates that the compiler cannot find the helper_functions.h file. This is because the #include <helper_functions.h> directive is looking for the file in the system's include paths, but the file is either not in those paths or is located in a different directory.
1. Use #include "helper_functions.h" Instead of #include <helper_functions.h>
Angle brackets (< >) are used for system or standard library headers.
Quotes (" ") are used for local or project-specific headers.
If helper_functions.h is in the same directory as cuda.cu, change the include directive to:
3. Verify the File Exists
Double-check that helper_functions.h exists in the specified location. If the file is missing, you'll need to obtain or recreate it.
4. Use the Correct CUDA Samples Path (if applicable)
If helper_functions.h is part of the CUDA Samples, ensure you have the CUDA Samples installed and include the correct path. For example, on Linux, the CUDA Samples are typically located in /usr/local/cuda/samples/common/inc. You can include this path like so:
Use #include "helper_functions.h" for local files.
Use the -I flag to specify the directory containing helper_functions.h.
Ensure the file exists in the specified location.
    """
    memory.push('assistant', sample_text)

    print("\n---\nmemory before:", memory.get())
    memory.compress()
    print("\n---\nmemory after:", memory.get())
    #memory.save_memory()
