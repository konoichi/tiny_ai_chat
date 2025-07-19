# NavyYard Chatbot

NavyYard is a modular, local AI chatbot system designed to run entirely on the user's machine without cloud dependencies. It's built with a focus on:

- **Modularity**: Clean separation of components for easy extension
- **Professional Logging & Debugging**: Comprehensive error handling and debug capabilities
- **Dynamic Personas**: Ability to switch between different chatbot personalities
- **Contextual Memory**: Conversation history management

The chatbot (nicknamed "Abby") provides an interactive command-line interface where users can have conversations with different AI personas powered by local LLM models (GGUF format) with GPU acceleration via llama-cpp-python.

## Key Features

- Streaming text output (token by token)
- Multiple switchable personas (Abby, Sage, Queen, McGee, Tammy)
- Colored terminal output for better readability
- Conversation history management
- Debug mode for model performance monitoring
- Self-test functionality
- Dynamic model switching