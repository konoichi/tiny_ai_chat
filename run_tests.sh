#!/bin/bash
# Run unit tests for NavyYard Chatbot

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Try to find pytest in common locations
PYTEST_CMD=""
if [ -f "/home/stephan/.local/bin/pytest" ]; then
    PYTEST_CMD="/home/stephan/.local/bin/pytest"
elif [ -f ".venv/bin/pytest" ]; then
    PYTEST_CMD=".venv/bin/pytest"
elif command -v pytest &> /dev/null; then
    PYTEST_CMD="pytest"
else
    echo "Error: pytest not found. Make sure it's installed in your environment."
    exit 1
fi

echo "Using pytest: $PYTEST_CMD"

# Run tests with pytest
$PYTEST_CMD tests/ -v

# Exit with pytest's exit code
exit $?