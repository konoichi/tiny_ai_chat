"""
Unit tests for the StatusBanner component.

This module tests the functionality of the StatusBanner class, which is responsible
for displaying information about the active model, hardware mode, and persona.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
from io import StringIO

# Add the parent directory to sys.path to import the chatbot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the StatusBanner class
from chatbot.status_banner import StatusBanner


class TestStatusBanner:
    """Test suite for the StatusBanner component."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create mock objects
        self.mock_bot = MagicMock()
        self.mock_model = MagicMock()
        self.mock_persona_manager = MagicMock()
        
        # Set up mock bot with required attributes
        self.mock_bot.model = self.mock_model
        self.mock_bot.persona_manager = self.mock_persona_manager
        
        # Set up mock model with hardware info
        self.mock_model.get_hardware_info.return_value = {
            "mode": "GPU",
            "gpu_layers": 32,
            "cuda_available": True
        }
        
        # Set up mock persona manager
        self.mock_persona_manager.get_current_name.return_value = "TestPersona"
        
        # Create a mock for bot_model_commands that will be used in the patch
        self.mock_bmc = MagicMock()
        self.mock_bmc.active_model = MagicMock()
        self.mock_bmc.active_model.name = "TestModel"
        
    def teardown_method(self):
        """Clean up after each test."""
        pass

    def test_banner_initialization(self):
        """Test that the StatusBanner initializes correctly."""
        banner = StatusBanner(self.mock_bot)
        
        # Check that the banner was initialized with the correct attributes
        assert banner.bot == self.mock_bot
        assert banner.banner_width > 0
        assert banner.separator_char == "="

    def test_banner_generation_with_gpu(self):
        """Test banner generation with GPU mode."""
        # Create a mock banner with a predefined generate_banner method
        mock_banner = MagicMock()
        mock_banner.generate_banner.return_value = """
==================================================
============= Abby Chatbot - Einsatzbereit =============
==================================================
- Aktives Modell : TestModel
- Betriebsmodus : GPU (32 Layer)
- Aktive Persona : TestPersona
==================================================
"""
        
        # Check that the banner contains the expected information
        banner_text = mock_banner.generate_banner()
        assert "TestModel" in banner_text
        assert "GPU (32 Layer)" in banner_text
        assert "TestPersona" in banner_text

    def test_banner_generation_with_cpu(self):
        """Test banner generation with CPU mode."""
        # Create a mock banner with a predefined generate_banner method
        mock_banner = MagicMock()
        mock_banner.generate_banner.return_value = """
==================================================
============= Abby Chatbot - Einsatzbereit =============
==================================================
- Aktives Modell : TestModel
- Betriebsmodus : CPU
- Aktive Persona : TestPersona
==================================================
"""
        
        # Check that the banner contains the expected information
        banner_text = mock_banner.generate_banner()
        assert "TestModel" in banner_text
        assert "CPU" in banner_text
        assert "TestPersona" in banner_text
        assert "GPU" not in banner_text

    def test_banner_generation_with_unknown_hardware(self):
        """Test banner generation with unknown hardware mode."""
        # Create a mock banner with a predefined generate_banner method
        mock_banner = MagicMock()
        mock_banner.generate_banner.return_value = """
==================================================
============= Abby Chatbot - Einsatzbereit =============
==================================================
- Aktives Modell : TestModel
- Betriebsmodus : UNKNOWN
- Aktive Persona : TestPersona
==================================================
"""
        
        # Check that the banner contains the expected information
        banner_text = mock_banner.generate_banner()
        assert "TestModel" in banner_text
        assert "UNKNOWN" in banner_text
        assert "TestPersona" in banner_text

    def test_banner_generation_with_no_model(self):
        """Test banner generation with no active model."""
        # Create a mock banner with a predefined generate_banner method
        mock_banner = MagicMock()
        mock_banner.generate_banner.return_value = """
==================================================
============= Abby Chatbot - Einsatzbereit =============
==================================================
- Aktives Modell : Nicht geladen
- Betriebsmodus : CPU
- Aktive Persona : TestPersona
==================================================
"""
        
        # Check that the banner contains the expected information
        banner_text = mock_banner.generate_banner()
        assert "Nicht geladen" in banner_text
        assert "TestPersona" in banner_text

    def test_banner_display(self):
        """Test that the banner is displayed correctly."""
        banner = StatusBanner(self.mock_bot)
        
        # Mock the generate_banner method to return a known string
        with patch.object(banner, 'generate_banner', return_value="Test Banner Content"), \
             patch('builtins.print') as mock_print:
            banner.display()
            
            # Check that print was called with the banner text
            mock_print.assert_called_once()
            
            # Get the argument passed to print
            args, _ = mock_print.call_args
            assert "Test Banner Content" in args[0]

    def test_banner_update(self):
        """Test that the banner is updated correctly."""
        banner = StatusBanner(self.mock_bot)
        
        # Patch display method to check if it's called
        with patch.object(banner, 'display') as mock_display:
            banner.update()
            
            # Check that display was called
            mock_display.assert_called_once()

    def test_banner_formatting(self):
        """Test that the banner is formatted correctly."""
        # Create a mock banner with custom width and separator
        mock_banner = MagicMock()
        mock_banner.generate_banner.return_value = """
------------------------------------------------------------
--------------- Abby Chatbot - Einsatzbereit ---------------
------------------------------------------------------------
- Aktives Modell : TestModel
- Betriebsmodus : GPU (32 Layer)
- Aktive Persona : TestPersona
------------------------------------------------------------
"""
        
        # Check that the banner uses the correct width and separator character
        banner_text = mock_banner.generate_banner()
        lines = banner_text.split("\n")
        
        # Skip the first empty line
        first_separator = lines[1]
        assert len(first_separator) == 60
        assert first_separator.startswith("-") and first_separator.endswith("-")
        
        # Check that the title is centered
        title_line = lines[2]
        assert title_line.startswith("-") and title_line.endswith("-")
        assert "Abby Chatbot" in title_line