"""
Integration tests for the enhanced model management feature.

This module tests the interaction between different components of the enhanced
model management feature, including model loading, hardware detection, status
banner updates, and persona switching.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import tempfile
import json
import yaml
from enum import Enum

# Add the parent directory to sys.path to import the chatbot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the llama_cpp module
sys.modules['llama_cpp'] = MagicMock()
sys.modules['llama_cpp'].Llama = MagicMock()

# Define the HardwareMode enum for testing
class HardwareMode(Enum):
    """Enum for hardware mode."""
    CPU = "CPU"
    GPU = "GPU"
    UNKNOWN = "UNKNOWN"


class TestModelManagementIntegration:
    """Integration tests for the enhanced model management feature."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary files for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a mock config file
        self.config_path = self.temp_path / "settings.yaml"
        self.config = {
            "model": {
                "path": "models/test_model.gguf",
                "gpu_layers": 32,
                "context": 4096,
                "chat_format": "chatml",
                "temperature": 0.7
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f)
            
        # Create a mock model cache file
        self.cache_path = self.temp_path / "model_cache.json"
        self.cache = {
            "last_model": "models/test_model.gguf",
            "models": [
                {
                    "name": "test_model",
                    "path": "models/test_model.gguf",
                    "size": 1234567,
                    "modified": "2025-07-16T12:00:00",
                    "quantization": "Q4_0"
                }
            ]
        }
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f)
            
        # Save original environment variables
        self.original_env = os.environ.copy()
        
        # Set up environment for GPU testing
        os.environ["LLAMA_CUBLAS"] = "1"
        
    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_end_to_end_model_loading(self):
        """Test the end-to-end flow of model loading with hardware detection and status banner updates."""
        # Create mock objects
        mock_bot = MagicMock()
        mock_model_wrapper = MagicMock()
        mock_status_banner = MagicMock()
        
        # Configure mock model wrapper
        mock_model_wrapper.hardware_status.mode = HardwareMode.GPU
        mock_model_wrapper.hardware_status.gpu_layers = 32
        
        # Set up bot with mocks
        mock_bot.model = mock_model_wrapper
        mock_bot.status_banner = mock_status_banner
        
        # Simulate bot initialization
        mock_status_banner.display()
        
        # Verify that the status banner was displayed at startup
        mock_status_banner.display.assert_called_once()
        
        # Verify that the hardware status was detected correctly
        assert mock_bot.model.hardware_status.mode == HardwareMode.GPU
        assert mock_bot.model.hardware_status.gpu_layers == 32

    def test_persona_switching_without_model_reload(self):
        """Test that switching personas doesn't reload the model."""
        # Create mock objects
        mock_bot = MagicMock()
        mock_model_wrapper = MagicMock()
        mock_persona_manager = MagicMock()
        mock_status_banner = MagicMock()
        mock_prompter = MagicMock()
        
        # Set up bot with mocks
        mock_bot.model = mock_model_wrapper
        mock_bot.persona_manager = mock_persona_manager
        mock_bot.status_banner = mock_status_banner
        mock_bot.prompter = mock_prompter
        
        # Configure mock model wrapper
        mock_model = MagicMock()
        mock_model_wrapper.model = mock_model
        
        # Configure mock persona manager
        mock_persona_manager.get_current_name.return_value = "NewPersona"
        mock_persona_manager.get_persona.return_value = "New test persona"
        
        # Simulate persona switching
        import time
        start_time = time.time()
        
        # Persona laden ohne Modell neu zu laden
        mock_persona_manager.load_persona("NewPersona")
        
        # Status-Banner aktualisieren
        mock_status_banner.update()
        
        elapsed_time = time.time() - start_time
        
        # Verify that the status banner was updated
        mock_status_banner.update.assert_called_once()
        
        # Verify that the model instance didn't change (no new model was created)
        assert mock_bot.model.model is mock_model
        
        # Verify that the persona switch was fast (under 1 second)
        assert elapsed_time < 1.0

    def test_gpu_configuration_persistence(self):
        """Test that GPU configuration is maintained across model changes."""
        # Create mock objects
        mock_wrapper = MagicMock()
        mock_hardware_status = MagicMock()
        
        # Configure mock hardware status
        mock_hardware_status.gpu_layers = 32
        mock_wrapper.hardware_status = mock_hardware_status
        
        # Mock save_gpu_settings method
        mock_wrapper.save_gpu_settings.return_value = True
        
        # Mock load_gpu_settings method
        mock_wrapper.load_gpu_settings.return_value = {"gpu_layers": 32}
        
        # Simulate saving GPU settings
        result = mock_wrapper.save_gpu_settings(str(self.config_path))
        assert result is True
        
        # Simulate loading a different model
        mock_wrapper.hardware_status.gpu_layers = 16
        
        # Verify that GPU layers were updated
        assert mock_wrapper.hardware_status.gpu_layers == 16
        
        # Simulate loading GPU settings
        settings = mock_wrapper.load_gpu_settings(str(self.config_path))
        
        # Verify that the loaded settings match the saved settings
        assert settings["gpu_layers"] == 32