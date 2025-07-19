"""
/chatbot/model_manager.py
Version: 1.2.0
------------------------------
Verwaltet das dynamische Laden und Auflisten von GGUF-Modellen inkl. Metadaten.

Dieses Modul ist verantwortlich für:
- Scannen des Modellverzeichnisses nach verfügbaren GGUF-Modellen
- Extrahieren und Caching von Modell-Metadaten (Kontext, Quantisierung, Architektur)
- Verwaltung des zuletzt verwendeten Modells
- Bereitstellung von Modell-Informationen für die Benutzeroberfläche

Das Modul verwendet einen Cache-Mechanismus, um wiederholte Metadaten-Extraktionen
zu vermeiden und die Startzeit zu verbessern. Wenn keine Metadaten verfügbar sind,
wird ein Fallback-Parsing des Dateinamens durchgeführt.

Erweiterungen:
- Liest `.gguf`-Metadaten (Kontext, Quantisierung, Architektur) aus Cache
- Fallback-Parsing aus Dateinamen
- Verwendet `model_cache.json` zur Beschleunigung

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from .model_metadata_cache import get_or_parse_model_metadata, read_cache, write_cache
from .config import SETTINGS

# Pfade
MODEL_DIR = Path("models")
CACHE_PATH = Path("model_cache.json")
LAST_MODEL_PATH = Path(".last_model")

@dataclass
class ModelInfo:
    """
    Datenklasse zur Speicherung von Modellinformationen.
    
    Diese Klasse speichert alle relevanten Informationen zu einem GGUF-Modell,
    einschließlich Metadaten wie Kontextlänge, Quantisierung und Architektur.
    Sie wird verwendet, um Modellinformationen zwischen verschiedenen Teilen
    des Systems zu übertragen.
    
    Attributes:
        index (int): Numerischer Index des Modells in der Liste
        name (str): Name des Modells (ohne Pfad und Erweiterung)
        path (Path): Vollständiger Pfad zur Modelldatei
        context_length (Optional[int]): Maximale Kontextlänge in Tokens
        quantization (Optional[str]): Quantisierungsformat (z.B. Q4_0, Q5_K_M)
        architecture (Optional[str]): Modellarchitektur (z.B. llama, mistral)
    """
    index: int
    name: str
    path: Path
    context_length: Optional[int] = None
    quantization: Optional[str] = None
    architecture: Optional[str] = None


def parse_fallback(name: str) -> (Optional[str], Optional[str]):
    """
    Extrahiert Quantisierung und Architektur aus dem Modellnamen als Fallback.
    
    Diese Funktion wird verwendet, wenn keine expliziten Metadaten für ein Modell
    verfügbar sind. Sie versucht, Informationen aus dem Dateinamen zu extrahieren,
    basierend auf gängigen Namenskonventionen für GGUF-Modelle.
    
    Args:
        name (str): Name des Modells (ohne Pfad)
        
    Returns:
        tuple: (quantization, architecture) - Beide können None sein, wenn nicht erkannt
    """
    quant = None
    arch = None
    if "." in name:
        prefix, quant = name.rsplit(".", 1)
    else:
        prefix = name
    if "-" in prefix:
        arch = prefix.rsplit("-", 1)[-1]
    return quant, arch


def scan_models() -> List[ModelInfo]:
    """
    Scannt das Modellverzeichnis nach GGUF-Dateien und erstellt ModelInfo-Objekte.
    
    Diese Funktion durchsucht das konfigurierte Modellverzeichnis nach GGUF-Dateien,
    extrahiert Metadaten (entweder aus dem Cache oder durch Parsing) und erstellt
    für jedes gefundene Modell ein ModelInfo-Objekt. Die Metadaten werden im Cache
    gespeichert, um zukünftige Aufrufe zu beschleunigen.
    
    Returns:
        List[ModelInfo]: Liste aller gefundenen Modelle mit Metadaten
    """
    files = sorted(MODEL_DIR.rglob("*.gguf"))
    cache = read_cache()
    models: List[ModelInfo] = []
    for i, f in enumerate(files):
        meta = get_or_parse_model_metadata(f, cache)
        name = f.stem
        # Metadaten oder Fallback
        quant = meta.get("quantization")
        arch = meta.get("architecture")
        ctx = meta.get("context_length")
        fb_quant, fb_arch = parse_fallback(name)
        if not quant:
            quant = fb_quant
        if not arch:
            arch = fb_arch
        if ctx is None:
            ctx = getattr(SETTINGS, "context", 4096)
        models.append(
            ModelInfo(
                index=i+1,
                name=name,
                path=f,
                context_length=ctx,
                quantization=quant,
                architecture=arch
            )
        )
    write_cache(cache)
    return models


def save_last_model(model: ModelInfo):
    """
    Speichert Informationen über das zuletzt verwendete Modell.
    
    Diese Funktion schreibt die Informationen des aktuell verwendeten Modells
    in eine Datei, damit es beim nächsten Start automatisch geladen werden kann.
    
    Args:
        model (ModelInfo): Das zu speichernde Modell
    """
    data = {
        "model_index": model.index,
        "model_path": str(model.path)
    }
    with open(LAST_MODEL_PATH, "w") as f:
        json.dump(data, f)


def load_last_model(models: List[ModelInfo]) -> Optional[ModelInfo]:
    """
    Lädt Informationen über das zuletzt verwendete Modell.
    
    Diese Funktion liest die gespeicherten Informationen des zuletzt verwendeten
    Modells und versucht, das entsprechende ModelInfo-Objekt aus der aktuellen
    Modellliste zu finden.
    
    Args:
        models (List[ModelInfo]): Liste der verfügbaren Modelle
        
    Returns:
        Optional[ModelInfo]: Das zuletzt verwendete Modell oder None, wenn nicht gefunden
    """
    if not LAST_MODEL_PATH.exists():
        return None
    with open(LAST_MODEL_PATH) as f:
        data = json.load(f)
    for m in models:
        if str(m.path) == data.get("model_path"):
            return m
    return None


def get_model_by_index(index: int, models: List[ModelInfo]) -> Optional[ModelInfo]:
    """
    Findet ein Modell anhand seines Index in der Modellliste.
    
    Diese Funktion wird verwendet, um ein Modell basierend auf dem vom Benutzer
    angegebenen Index zu finden, z.B. bei Verwendung des !model <n> Befehls.
    
    Args:
        index (int): Der zu suchende Index
        models (List[ModelInfo]): Liste der verfügbaren Modelle
        
    Returns:
        Optional[ModelInfo]: Das gefundene Modell oder None, wenn kein Modell mit diesem Index existiert
    """
    for m in models:
        if m.index == index:
            return m
    return None
