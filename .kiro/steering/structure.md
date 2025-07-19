# NavyYard Project Structure

## Directory Organization

```
navyyard/
├── .kiro/                  # Kiro assistant configuration
├── .venv/                  # Python virtual environment (created by run.sh)
├── chatbot/                # Core chatbot functionality
│   ├── __pycache__/        # Python cache files
│   ├── commands/           # Command handling modules
│   │   ├── __pycache__/
│   │   └── model_list_command.py
│   ├── utils/              # Utility functions
│   │   ├── __pycache__/
│   │   └── ram_estimator.py
│   ├── bot.py              # Main chatbot class (AbbyBot)
│   ├── bot_model_commands.py # Model-related commands
│   ├── config.py           # Global settings
│   ├── error_handler.py    # Error handling and logging
│   ├── memory.py           # Conversation history management
│   ├── model_manager.py    # Model discovery and management
│   ├── model_metadata_cache.py # Model metadata caching
│   ├── model_wrapper.py    # LLM interface wrapper
│   ├── persona_manager.py  # Persona loading and switching
│   ├── prompter.py         # Prompt construction
│   └── selftest.py         # System self-test functionality
├── config/                 # Configuration files
│   ├── abby.txt            # Persona definition for Abby
│   ├── mcgee.txt           # Persona definition for McGee
│   ├── queen.txt           # Persona definition for Queen
│   ├── sage.txt            # Persona definition for Sage
│   ├── settings.yaml       # Main configuration file
│   └── tammy.txt           # Persona definition for Tammy
├── models/                 # GGUF model files
│   ├── dolphin-2.2.1-mistral-7b.Q4_0.gguf
│   ├── dolphin-2.2.1-mistral-7b.Q5_0.gguf
│   └── tinyllama-1.1b-chat-v1.0.Q8_0.gguf
├── main.py                 # Application entry point
├── model_cache.json        # Cache for model metadata
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── run.sh                  # Setup and execution script
└── various GPU test files  # Utilities for GPU testing
```

## Key Components

### Core Modules

- **bot.py**: Main controller class (AbbyBot) that orchestrates all components
- **model_wrapper.py**: Interface to llama-cpp-python for model interaction
- **memory.py**: Manages conversation history
- **prompter.py**: Builds prompts from persona definitions and conversation history
- **persona_manager.py**: Loads and manages different chatbot personalities
- **config.py**: Global settings and configuration
- **error_handler.py**: Centralized error handling and logging

### Configuration

- **settings.yaml**: Main configuration file with model paths and parameters
- **Persona files (*.txt)**: Text files defining different chatbot personalities

### Entry Points

- **main.py**: Application entry point that sets environment variables and starts the bot
- **run.sh**: Shell script for environment setup and launching the application

## Architecture Pattern

The project follows a modular architecture with clear separation of concerns:

1. **Main Controller**: AbbyBot class orchestrates all components
2. **Service Modules**: Specialized classes for specific functionality (model, memory, personas)
3. **Configuration**: External configuration files for settings and personas
4. **Error Handling**: Centralized error handling with custom exception types

This design allows for easy extension and modification of individual components without affecting the rest of the system.