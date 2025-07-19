# Design Document

## Overview

This document outlines the design for simplifying the Coqui TTS integration in the NavyYard chatbot. The current implementation is complex and has reliability issues, particularly with GPU detection and initialization. The simplified approach will focus on creating a minimal, reliable implementation that maintains compatibility with the existing system while being easier to maintain and debug.

## Architecture

The simplified TTS Coqui integration will maintain the existing architecture of the TTS system, which consists of:

1. **TTSManager**: Central manager class that handles TTS configuration, engine selection, and speech operations
2. **TTSEngineBase**: Abstract base class defining the interface for all TTS engines
3. **Concrete Engine Implementations**: Including the simplified CoquiTTSEngine

The key change will be replacing the complex CoquiTTSEngine implementation with a simplified version that focuses on reliability and maintainability.

## Components and Interfaces

### SimpleCoquiTTSEngine

The core of the simplified implementation will be the `SimpleCoquiTTSEngine` class, which will:

1. Implement the `TTSEngineBase` interface
2. Provide a minimal implementation focused on reliability
3. Handle GPU configuration gracefully
4. Use proper error handling and logging

```python
class SimpleCoquiTTSEngine(TTSEngineBase):
    """
    Simplified Coqui TTS engine implementation that focuses on reliability
    """
    
    def __init__(self, rate: int = 200, voice_id: Optional[str] = None, 
                 model_name: str = "tts_models/de/thorsten/tacotron2-DDC",
                 speaker_idx: int = 0, vocoder_name: Optional[str] = None,
                 use_gpu: bool = False):
        """Initialize the Coqui TTS engine"""
        super().__init__(rate, voice_id)
        self.model_name = model_name
        self.speaker_idx = speaker_idx
        self.vocoder_name = vocoder_name
        self.use_gpu = use_gpu
        self.tts = None
        self._speaking = False
        self._speech_lock = threading.Lock()
        
        # Initialize the TTS engine
        self._initialize_tts()
    
    # Other methods implementing the TTSEngineBase interface
```

### Integration with TTSManager

The `TTSManager` class will need to be modified to use the simplified engine. This will be done through a patching mechanism that replaces the engine selection logic:

```python
def apply_fix():
    """
    Apply the fix to use the simplified TTS engine
    """
    # Import the TTS manager
    from chatbot.tts_manager import TTSManager
    
    # Create a monkey patch for the TTS manager
    original_get_engine_class = TTSManager._get_engine_class
    
    def patched_get_engine_class(self):
        """
        Patched method that returns SimpleCoquiTTSEngine when coqui is requested
        """
        if self.config.engine == "coqui":
            return SimpleCoquiTTSEngine
        else:
            # Call the original method for other engines
            return original_get_engine_class(self)
    
    # Apply the patch
    TTSManager._get_engine_class = patched_get_engine_class
```

## Data Models

The simplified implementation will maintain compatibility with the existing data models:

1. **Voice**: Represents a TTS voice with id, name, gender, and language
2. **TTSConfig**: Configuration settings for TTS functionality

No changes to these data models are required for the simplification.

## Error Handling

The simplified implementation will focus on improved error handling:

1. **Graceful Initialization**: Handle errors during TTS initialization without crashing
2. **Detailed Logging**: Provide detailed error messages for debugging
3. **Fallback Mechanisms**: Automatically fall back to CPU mode if GPU causes issues
4. **Recovery**: Recover from errors during speech generation

## Testing Strategy

The testing strategy will include:

1. **Unit Tests**: Test the SimpleCoquiTTSEngine in isolation
2. **Integration Tests**: Test the integration with TTSManager
3. **Manual Testing**: Test the functionality with different configurations
4. **Diagnostic Tools**: Create diagnostic tools to help identify issues

## Implementation Plan

The implementation will follow these steps:

1. Create a backup of the current implementation
2. Implement the SimpleCoquiTTSEngine class
3. Create the patching mechanism to integrate with TTSManager
4. Update the configuration handling
5. Implement diagnostic tools
6. Test the implementation thoroughly
7. Deploy the changes

## Considerations

### GPU Handling

Special attention will be paid to GPU handling, as this is a common source of issues:

1. Respect the use_gpu configuration setting
2. Disable CUDA explicitly when not using GPU
3. Handle GPU-related errors gracefully
4. Provide clear error messages for GPU issues

### Backward Compatibility

The simplified implementation must maintain backward compatibility:

1. Implement the same interface as the existing CoquiTTSEngine
2. Maintain compatibility with persona voice settings
3. Support the same configuration options
4. Handle the same TTS commands