# Design Document

## Overview

The TTS Complete Removal design outlines the systematic elimination of all Text-to-Speech functionality from the NavyYard chatbot project. This involves removing TTS-specific files, cleaning imports and references, updating configuration files, removing dependencies, and ensuring the remaining system functions correctly without any TTS components.

The design follows a comprehensive approach to ensure no TTS remnants remain in the codebase, configuration, documentation, or dependencies. The removal process is structured to maintain system integrity while completely eliminating TTS functionality.

## Architecture

### Current TTS Architecture (To Be Removed)

The current TTS system consists of:

1. **Core TTS Components**:
   - `chatbot/tts_manager.py` - Main TTS management class
   - `chatbot/tts_engines.py` - TTS engine implementations
   - `chatbot/tts_persona_integration.py` - Integration with persona system
   - `chatbot/commands/tts_commands.py` - TTS command handlers

2. **Integration Points**:
   - `chatbot/bot.py` - Main bot class with TTS initialization and usage
   - `main.py` - Application entry point (potential TTS references)
   - Configuration files with TTS settings

3. **Dependencies**:
   - Coqui TTS (`TTS>=0.22.0`)
   - PyTorch for TTS (`torch>=2.0.0`, `torchaudio>=2.0.0`)
   - Platform-specific TTS libraries (`pyttsx3>=2.90`)
   - Audio processing libraries (`librosa`, `soundfile`, etc.)

4. **Test Files**:
   - `test_tts_cpu_fix.py` - TTS-specific test file
   - TTS-related test methods in other test files

### Target Architecture (After Removal)

The cleaned architecture will have:

1. **Core Chat Components** (Unchanged):
   - `chatbot/bot.py` - Main bot class without TTS functionality
   - `chatbot/model_wrapper.py` - LLM interface
   - `chatbot/persona_manager.py` - Persona management
   - `chatbot/memory.py` - Conversation history
   - `chatbot/prompter.py` - Prompt construction

2. **Configuration** (Cleaned):
   - `config/settings.yaml` - Without TTS configuration section
   - Persona files without voice-related settings

3. **Dependencies** (Reduced):
   - Only core chatbot dependencies
   - No TTS-specific packages

## Components and Interfaces

### Files to be Deleted

1. **TTS Core Files**:
   - `chatbot/tts_manager.py`
   - `chatbot/tts_engines.py`
   - `chatbot/tts_persona_integration.py`
   - `chatbot/commands/tts_commands.py`

2. **TTS Test Files**:
   - `test_tts_cpu_fix.py`
   - Any TTS-related test methods in other test files

### Files to be Modified

1. **Main Application Files**:
   - `chatbot/bot.py` - Remove TTS imports, initialization, and usage
   - `main.py` - Remove any TTS-related imports or setup

2. **Configuration Files**:
   - `config/settings.yaml` - Remove TTS configuration section
   - Persona files - Remove voice-related settings

3. **Dependency Files**:
   - `requirements.txt` - Remove TTS-related dependencies
   - `run.sh` - Remove TTS-related installation steps (if any)

4. **Documentation Files**:
   - `README.md` - Remove TTS feature references
   - `docs/TTS_SETUP.md` - Delete if exists
   - Help text and command documentation

### Integration Points to Clean

1. **Bot Class (`chatbot/bot.py`)**:
   - Remove TTS manager initialization
   - Remove TTS persona integration
   - Remove TTS command handling
   - Remove TTS usage in chat responses
   - Remove TTS streaming functionality

2. **Command System**:
   - Remove `!tts` command handling
   - Update help text to exclude TTS commands
   - Remove TTS-related error handling

3. **Configuration System**:
   - Remove TTS configuration loading
   - Remove TTS settings validation
   - Clean default configuration values

## Data Models

### Configuration Changes

**Before (TTS Configuration)**:
```yaml
tts:
  enabled: false
  engine: auto
  default_voice: null
  rate: 200
  coqui:
    model_name: tts_models/de/thorsten/tacotron2-DDC
    speaker_idx: 0
    use_gpu: true
    model_cache_dir: models/tts
    download_models: true
```

**After (No TTS Configuration)**:
```yaml
# TTS section completely removed
```

### Persona Configuration Changes

**Before (With Voice Settings)**:
```yaml
persona:
  name: "Abby"
  voice_id: "some_voice_id"
  speech_rate: 200
```

**After (Without Voice Settings)**:
```yaml
persona:
  name: "Abby"
  # voice_id and speech_rate removed
```

### Dependency Changes

**Before (With TTS Dependencies)**:
```txt
# Text-to-Speech dependencies
pyttsx3>=2.90
TTS>=0.22.0
torch>=2.0.0
torchaudio>=2.0.0
librosa>=0.10.0
soundfile>=0.12.0
inflect>=6.0.0
unidecode>=1.3.0
```

**After (Without TTS Dependencies)**:
```txt
# TTS dependencies completely removed
```

## Error Handling

### TTS Error Removal Strategy

1. **Remove TTS-Specific Exceptions**:
   - Remove `TTSError` class from `tts_manager.py`
   - Remove TTS-related error handling in bot.py
   - Remove TTS error logging and status messages

2. **Clean Error Handling in Bot Class**:
   - Remove try-catch blocks around TTS initialization
   - Remove TTS-related error messages and warnings
   - Remove TTS availability checks and fallbacks

3. **Update Status and Debug Information**:
   - Remove TTS status from system status displays
   - Remove TTS-related debug output
   - Remove TTS performance monitoring

### Graceful Degradation Removal

Since TTS is being completely removed, all graceful degradation logic related to TTS will be eliminated:
- No fallback TTS engines
- No TTS availability checks
- No TTS error recovery mechanisms

## Testing Strategy

### Test Cleanup Approach

1. **Remove TTS-Specific Test Files**:
   - Delete `test_tts_cpu_fix.py`
   - Remove any TTS integration tests

2. **Clean Existing Test Files**:
   - Remove TTS-related test methods from integration tests
   - Remove TTS mocking and setup code
   - Update test assertions to not expect TTS functionality

3. **Update System Tests**:
   - Remove TTS checks from selftest functionality
   - Update system validation to not require TTS
   - Remove TTS from CI/CD pipeline tests

### Validation Testing

1. **Functionality Tests**:
   - Verify all non-TTS commands work correctly
   - Verify persona switching works without voice settings
   - Verify chat functionality is unaffected

2. **Configuration Tests**:
   - Verify application starts without TTS configuration
   - Verify configuration loading works with cleaned settings
   - Verify no TTS-related errors or warnings appear

3. **Dependency Tests**:
   - Verify application runs without TTS dependencies
   - Verify installation process works with reduced requirements
   - Verify no import errors for removed TTS modules

### Integration Testing

1. **Bot Integration**:
   - Test complete chat workflows without TTS
   - Verify streaming mode works without TTS integration
   - Test persona switching without voice changes

2. **Command System**:
   - Verify help system doesn't reference TTS commands
   - Test error handling for removed commands
   - Verify command parsing works correctly

3. **Configuration Integration**:
   - Test configuration loading and saving
   - Verify persona management without voice settings
   - Test system initialization without TTS components

## Implementation Phases

### Phase 1: File Removal
- Delete TTS-specific Python files
- Remove TTS test files
- Clean up any TTS-related cache or temporary files

### Phase 2: Code Cleanup
- Remove TTS imports from all remaining files
- Remove TTS initialization and usage code
- Clean TTS-related methods and classes

### Phase 3: Configuration Cleanup
- Remove TTS sections from configuration files
- Clean persona configurations
- Update default settings

### Phase 4: Dependency Cleanup
- Remove TTS dependencies from requirements.txt
- Update installation scripts
- Clean build and setup processes

### Phase 5: Documentation Cleanup
- Update README and documentation
- Remove TTS from feature lists
- Update help text and command documentation

### Phase 6: Testing and Validation
- Run comprehensive tests
- Verify system functionality
- Validate complete TTS removal

## Risk Mitigation

### Potential Issues and Solutions

1. **Broken Imports**: Systematic search and removal of all TTS imports
2. **Configuration Errors**: Careful removal of TTS configuration sections
3. **Command Parsing Issues**: Update command handlers to ignore TTS commands
4. **Integration Failures**: Thorough testing of all integration points

### Rollback Strategy

- Maintain backup of TTS files before deletion
- Document all changes for potential reversal
- Test system thoroughly before finalizing removal

## Success Criteria

1. **Complete Code Removal**: No TTS-related code remains in the project
2. **Clean Configuration**: No TTS settings in configuration files
3. **Dependency Cleanup**: No TTS dependencies in requirements
4. **Functional System**: All non-TTS functionality works correctly
5. **Clean Documentation**: No TTS references in documentation
6. **Successful Tests**: All tests pass without TTS components