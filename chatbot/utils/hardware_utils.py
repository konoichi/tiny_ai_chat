# /chatbot/hardware_utils.py
"""
Hardware-Hilfsfunktionen und Datenklassen.
Kapselt die Logik zur Erkennung und Verwaltung von Hardware-Ressourcen (CPU/GPU).
"""
import os
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any

logger = logging.getLogger("HardwareUtils")

class HardwareMode(Enum):
    """Enum für den Hardware-Modus des Modells."""
    CPU = "CPU"
    GPU = "GPU"
    UNKNOWN = "UNKNOWN"

@dataclass
class HardwareStatus:
    """Datenklasse zur Speicherung des Hardware-Status."""
    mode: HardwareMode = HardwareMode.UNKNOWN
    gpu_layers: int = 0
    cuda_available: bool = False
    last_checked: float = 0.0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

def check_cuda_availability() -> bool:
    """
    Prüft, ob eine CUDA-fähige Umgebung wahrscheinlich ist.
    Gibt True zurück, wenn CUDA-Indikatoren gefunden werden.
    """
    try:
        # Prüfe Umgebungsvariablen
        if "CUDA_VISIBLE_DEVICES" in os.environ and os.environ["CUDA_VISIBLE_DEVICES"] != "-1":
            logger.info("CUDA erkannt über CUDA_VISIBLE_DEVICES")
            return True
            
        if "LLAMA_CUBLAS" in os.environ and os.environ["LLAMA_CUBLAS"] == "1":
            logger.info("CUDA erkannt über LLAMA_CUBLAS=1")
            return True
            
        # Optional: Prüfe auf Existenz der Bibliothek (weniger zuverlässig)
        import ctypes
        ctypes.CDLL("libcudart.so")
        logger.info("CUDA-Bibliothek 'libcudart.so' gefunden")
        return True
    except (OSError, AttributeError, ImportError):
        # Fehler wird erwartet, wenn CUDA nicht da ist. Kein Grund zur Panik.
        logger.debug("Keine CUDA-Indikatoren gefunden.")
        return False

def ensure_gpu_config(cuda_available: bool) -> bool:
    """
    Stellt sicher, dass die Umgebungsvariablen für die GPU-Nutzung korrekt gesetzt sind.
    """
    if not cuda_available:
        logger.info("CUDA nicht verfügbar, keine GPU-Konfiguration nötig.")
        return True

    config_ok = True
    # Setze LLAMA_CUBLAS, falls nicht gesetzt
    if os.environ.get("LLAMA_CUBLAS") != "1":
        os.environ["LLAMA_CUBLAS"] = "1"
        logger.info("Umgebungsvariable LLAMA_CUBLAS auf '1' gesetzt.")

    # Korrigiere CUDA_VISIBLE_DEVICES, falls es GPU-Nutzung blockiert
    if os.environ.get("CUDA_VISIBLE_DEVICES") == "-1":
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        logger.info("CUDA_VISIBLE_DEVICES von '-1' auf '0' geändert, um GPU-Nutzung zu ermöglichen.")
    
    return config_ok