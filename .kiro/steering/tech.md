# NavyYard Technical Stack

## Core Technologies

- **Python 3.10+**: Primary programming language
- **llama-cpp-python**: Interface to LLM models with CUDA acceleration
- **GGUF Models**: Local language models in GGUF format
- **YAML**: Configuration file format
- **colorama**: Terminal text coloring

## Dependencies

- **Required**:
  - llama-cpp-python (with CUDA support)
  - numpy
  - pyyaml
  - colorama

- **Optional**:
  - loguru (enhanced logging)
  - tqdm (progress bars)
  - pytest (testing)

## Build System

The project uses a simple bash script (`run.sh`) for setup and execution that:
1. Checks for required build tools (cmake, autoconf)
2. Creates and manages a Python virtual environment
3. Installs llama-cpp-python with GPU support
4. Installs other dependencies from requirements.txt
5. Launches the application

## Common Commands

### Setup & Running

```bash
# First-time setup and run
chmod +x run.sh
./run.sh

# Subsequent runs
./run.sh
```

### In-Chat Commands

```
!persona <name>     - Switch active persona (abby, sage, queen, mcgee, tammy)
!stream on/off      - Enable/disable streaming mode
!reset              - Clear conversation history
!debug on/off       - Enable/disable debug mode
!status             - Display current status
!models [--verbose] - List available models
!model <n>          - Load model with index n
!model last_model   - Reload last used model
!model              - Show active model info
selftest            - Run system check
!help               - Show help
exit / quit         - Exit the chatbot
```

## GPU Acceleration

The system uses CUDA acceleration via the `LLAMA_CUBLAS=1` environment variable and custom compilation of llama-cpp-python with `-DGGML_CUDA=on` CMAKE flags.