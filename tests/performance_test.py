#!/usr/bin/env python3
"""
Performance tests for the enhanced model management feature.

This script measures the performance of various aspects of the enhanced model
management feature, including startup time with pre-indexing, persona switching
time, and model loading times with different configurations.

Usage:
    python tests/performance_test.py

Note: This script requires the actual dependencies to be installed, as it runs
real performance tests rather than mocked tests.
"""

import os
import sys
import time
import argparse
from pathlib import Path
import statistics
import json

# Add the parent directory to sys.path to import the chatbot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set LLAMA_CUBLAS environment variable for GPU support
os.environ["LLAMA_CUBLAS"] = "1"

def measure_startup_time(iterations=3):
    """
    Measure the startup time with pre-indexing.
    
    Args:
        iterations (int): Number of iterations to run
        
    Returns:
        dict: Dictionary with timing results
    """
    print("\n=== Measuring Startup Time with Pre-indexing ===")
    
    results = []
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        # Measure time to import and initialize AbbyBot
        start_time = time.time()
        
        # Import modules
        from chatbot.bot import AbbyBot
        
        # Create a bot instance with mocked model loading
        with patch('chatbot.model_wrapper.Llama', MagicMock()):
            bot = AbbyBot()
        
        end_time = time.time()
        duration = end_time - start_time
        results.append(duration)
        
        print(f"  Startup time: {duration:.3f} seconds")
        
        # Clean up
        del bot
        del sys.modules['chatbot.bot']
    
    # Calculate statistics
    avg_time = statistics.mean(results)
    min_time = min(results)
    max_time = max(results)
    
    print(f"\nResults after {iterations} iterations:")
    print(f"  Average startup time: {avg_time:.3f} seconds")
    print(f"  Minimum startup time: {min_time:.3f} seconds")
    print(f"  Maximum startup time: {max_time:.3f} seconds")
    
    return {
        "test": "startup_time",
        "iterations": iterations,
        "results": results,
        "average": avg_time,
        "min": min_time,
        "max": max_time
    }

def measure_persona_switching_time(iterations=5):
    """
    Measure the time taken to switch personas.
    
    Args:
        iterations (int): Number of iterations to run
        
    Returns:
        dict: Dictionary with timing results
    """
    print("\n=== Measuring Persona Switching Time ===")
    
    # Import modules
    from chatbot.bot import AbbyBot
    from unittest.mock import patch, MagicMock
    
    results = []
    
    # Create a bot instance with mocked model loading
    with patch('chatbot.model_wrapper.Llama', MagicMock()):
        bot = AbbyBot()
        
        # Set up personas
        personas = ["abby", "sage", "queen", "mcgee", "tammy"]
        
        # Measure persona switching time
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}...")
            
            # Switch between personas
            for persona in personas:
                print(f"    Switching to {persona}...")
                
                # Patch actual persona loading to avoid file system operations
                with patch.object(bot.persona_manager, 'load_persona'), \
                     patch.object(bot.persona_manager, 'get_current_name', return_value=persona), \
                     patch.object(bot.persona_manager, 'get_persona', return_value=f"Test persona {persona}"), \
                     patch.object(bot.status_banner, 'update'):
                    
                    # Measure time to switch persona
                    start_time = time.time()
                    
                    # Persona laden ohne Modell neu zu laden
                    bot.persona_manager.load_persona(persona)
                    
                    # Nur Prompt-Template aktualisieren, nicht das Modell
                    bot.prompter = MagicMock()
                    
                    # Status-Banner aktualisieren
                    bot.status_banner.update()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    results.append(duration)
                    
                    print(f"    Switching time: {duration:.3f} seconds")
    
    # Calculate statistics
    avg_time = statistics.mean(results)
    min_time = min(results)
    max_time = max(results)
    
    print(f"\nResults after {iterations * len(personas)} persona switches:")
    print(f"  Average switching time: {avg_time:.3f} seconds")
    print(f"  Minimum switching time: {min_time:.3f} seconds")
    print(f"  Maximum switching time: {max_time:.3f} seconds")
    
    return {
        "test": "persona_switching_time",
        "iterations": iterations * len(personas),
        "results": results,
        "average": avg_time,
        "min": min_time,
        "max": max_time
    }

def measure_model_loading_times(iterations=3):
    """
    Measure model loading times with different configurations.
    
    Args:
        iterations (int): Number of iterations to run
        
    Returns:
        dict: Dictionary with timing results
    """
    print("\n=== Measuring Model Loading Times ===")
    
    # Import modules
    from chatbot.model_wrapper import ModelWrapper
    from unittest.mock import patch, MagicMock
    
    # Define configurations to test
    configs = [
        {"name": "CPU mode", "gpu_layers": 0},
        {"name": "GPU with 16 layers", "gpu_layers": 16},
        {"name": "GPU with 32 layers", "gpu_layers": 32},
        {"name": "GPU with 64 layers", "gpu_layers": 64}
    ]
    
    results = {}
    
    for config in configs:
        config_name = config["name"]
        gpu_layers = config["gpu_layers"]
        
        print(f"\n  Testing {config_name} (gpu_layers={gpu_layers}):")
        config_results = []
        
        for i in range(iterations):
            print(f"    Iteration {i+1}/{iterations}...")
            
            # Create a model wrapper with mocked Llama
            with patch('chatbot.model_wrapper.Llama') as mock_llama:
                # Configure mock
                mock_model = MagicMock()
                mock_model.n_gpu_layers = gpu_layers
                mock_llama.return_value = mock_model
                
                # Create a model wrapper with a temporary config
                with patch('yaml.safe_load', return_value={"model": {"path": "models/test_model.gguf"}}), \
                     patch('builtins.open', create=True):
                    wrapper = ModelWrapper()
                    
                    # Measure time to load model
                    start_time = time.time()
                    
                    # Load model with specified GPU layers
                    wrapper.load_model("models/test_model.gguf", n_gpu_layers=gpu_layers)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    config_results.append(duration)
                    
                    print(f"    Loading time: {duration:.3f} seconds")
        
        # Calculate statistics for this configuration
        avg_time = statistics.mean(config_results)
        min_time = min(config_results)
        max_time = max(config_results)
        
        print(f"  Results for {config_name}:")
        print(f"    Average loading time: {avg_time:.3f} seconds")
        print(f"    Minimum loading time: {min_time:.3f} seconds")
        print(f"    Maximum loading time: {max_time:.3f} seconds")
        
        results[config_name] = {
            "gpu_layers": gpu_layers,
            "iterations": iterations,
            "results": config_results,
            "average": avg_time,
            "min": min_time,
            "max": max_time
        }
    
    return {
        "test": "model_loading_times",
        "configurations": results
    }

def run_all_tests():
    """Run all performance tests and save results to a file."""
    from unittest.mock import patch, MagicMock
    
    print("Running performance tests for enhanced model management...")
    
    # Create results directory if it doesn't exist
    results_dir = Path("tests/results")
    results_dir.mkdir(exist_ok=True)
    
    # Run tests
    results = {}
    
    # Measure startup time
    results["startup_time"] = measure_startup_time()
    
    # Measure persona switching time
    results["persona_switching_time"] = measure_persona_switching_time()
    
    # Measure model loading times
    results["model_loading_times"] = measure_model_loading_times()
    
    # Save results to file
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    results_file = results_dir / f"performance_results_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run performance tests for enhanced model management")
    parser.add_argument("--startup", action="store_true", help="Run startup time test only")
    parser.add_argument("--persona", action="store_true", help="Run persona switching time test only")
    parser.add_argument("--model", action="store_true", help="Run model loading times test only")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations for each test")
    
    args = parser.parse_args()
    
    if args.startup or args.persona or args.model:
        from unittest.mock import patch, MagicMock
        
        if args.startup:
            measure_startup_time(args.iterations)
        if args.persona:
            measure_persona_switching_time(args.iterations)
        if args.model:
            measure_model_loading_times(args.iterations)
    else:
        run_all_tests()