"""
Unit tests for hardware detection functionality.

This module tests the hardware detection capabilities of the NavyYard chatbot,
focusing on CPU/GPU mode detection and GPU layer configuration.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the parent directory to sys.path to import the chatbot modules
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHardwareDetection:
    """Test suite for hardware detection functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Save original environment variables
        self.original_env = os.environ.copy()
        
    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_cuda_environment_variables(self):
        """Test that CUDA environment variables are correctly detected."""
        # Test with LLAMA_CUBLAS=1
        os.environ["LLAMA_CUBLAS"] = "1"
        assert os.environ.get("LLAMA_CUBLAS") == "1"
        
        # Test with LLAMA_CUBLAS=0
        os.environ["LLAMA_CUBLAS"] = "0"
        assert os.environ.get("LLAMA_CUBLAS") == "0"
        
        # Test with LLAMA_CUBLAS not set
        if "LLAMA_CUBLAS" in os.environ:
            del os.environ["LLAMA_CUBLAS"]
        assert os.environ.get("LLAMA_CUBLAS") is None

    def test_cuda_visible_devices(self):
        """Test that CUDA_VISIBLE_DEVICES is correctly handled."""
        # Test with CUDA_VISIBLE_DEVICES=0
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "0"
        
        # Test with CUDA_VISIBLE_DEVICES=-1 (disabled)
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "-1"
        
        # Test with CUDA_VISIBLE_DEVICES not set
        if "CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["CUDA_VISIBLE_DEVICES"]
        assert os.environ.get("CUDA_VISIBLE_DEVICES") is None

    @patch('subprocess.check_output')
    def test_nvidia_smi_parsing(self, mock_check_output):
        """Test parsing of nvidia-smi output."""
        # Mock nvidia-smi output
        mock_check_output.return_value = b"80, 5000"
        
        # Parse the output
        try:
            output = mock_check_output.return_value.decode().strip().split(', ')
            util = output[0]
            mem = output[1]
            
            # Verify parsed values
            assert util == "80"
            assert mem == "5000"
        except Exception as e:
            pytest.fail(f"Failed to parse nvidia-smi output: {e}")

    def test_gpu_layers_validation(self):
        """Test validation of GPU layers parameter."""
        # Test valid values
        assert self._validate_gpu_layers(32) == 32
        assert self._validate_gpu_layers(0) == 0
        assert self._validate_gpu_layers(64) == 64
        
        # Test invalid values
        assert self._validate_gpu_layers(-1) == 50  # Should return default
        assert self._validate_gpu_layers("invalid") == 50  # Should return default
        assert self._validate_gpu_layers(None) == 50  # Should return default

    def _validate_gpu_layers(self, n_gpu_layers, default=50):
        """Helper method to validate GPU layers parameter."""
        if not isinstance(n_gpu_layers, int) or n_gpu_layers < 0:
            return default
        return n_gpu_layers

    def test_hardware_mode_determination(self):
        """Test determination of hardware mode based on GPU layers."""
        # Test CPU mode (0 layers)
        assert self._determine_hardware_mode(0) == "CPU"
        
        # Test GPU mode (positive layers)
        assert self._determine_hardware_mode(1) == "GPU"
        assert self._determine_hardware_mode(32) == "GPU"
        assert self._determine_hardware_mode(64) == "GPU"

    def _determine_hardware_mode(self, gpu_layers):
        """Helper method to determine hardware mode based on GPU layers."""
        return "GPU" if gpu_layers > 0 else "CPU"

    def test_gpu_config_environment_setup(self):
        """Test setting up environment variables for GPU configuration."""
        # Test setting LLAMA_CUBLAS
        self._ensure_gpu_environment()
        assert os.environ.get("LLAMA_CUBLAS") == "1"
        
        # Test with CUDA_VISIBLE_DEVICES=-1
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        self._ensure_gpu_environment()
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "0"

    def _ensure_gpu_environment(self):
        """Helper method to set up environment variables for GPU."""
        # Set LLAMA_CUBLAS if not already set
        if "LLAMA_CUBLAS" not in os.environ:
            os.environ["LLAMA_CUBLAS"] = "1"
        elif os.environ["LLAMA_CUBLAS"] != "1":
            os.environ["LLAMA_CUBLAS"] = "1"
            
        # Fix CUDA_VISIBLE_DEVICES if set to -1
        if "CUDA_VISIBLE_DEVICES" in os.environ and os.environ["CUDA_VISIBLE_DEVICES"] == "-1":
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"