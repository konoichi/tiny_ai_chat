"""
/chatbot/model_metadata_cache.py
Version: 1.0.0
------------------------------
Liest und cached Metadaten aus GGUF-Modellen.

Funktionen:
- `.gguf`-Header lesen (Kontext, Quantisierung, Architektur)
- Cache-Datei `model_cache.json` erzeugen und aktualisieren
- Bei erneutem Start: schnelle Nutzung des Caches

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

import struct
import json
from pathlib import Path
from typing import Dict, Optional

CACHE_PATH = Path("model_cache.json")

# Vereinfachtes Beispiel — genaue Struktur gguf je nach Format
KEYWORDS = [b"context_length", b"quantization", b"architecture"]


def parse_gguf_header(path: Path) -> Dict[str, Optional[str]]:
    meta = {"context_length": None, "quantization": None, "architecture": None}
    try:
        with path.open("rb") as f:
            content = f.read(4096)  # nur Header einlesen
            for key in KEYWORDS:
                idx = content.find(key)
                if idx != -1:
                    snippet = content[idx:idx+64]
                    parts = snippet.split(b"\x00")
                    meta[key.decode()] = parts[1].decode(errors="ignore").strip()
    except Exception:
        pass
    return meta


def read_cache() -> Dict[str, Dict]:
    """
    Liest den Modell-Metadaten-Cache aus der Cache-Datei.
    
    Diese Funktion liest den Cache aus der Datei und validiert ihn.
    Wenn die Datei nicht existiert oder ungültig ist, wird ein leerer Cache zurückgegeben.
    
    Returns:
        Dict[str, Dict]: Der geladene Cache oder ein leeres Dictionary
    """
    if not CACHE_PATH.exists():
        return {}
        
    try:
        with open(CACHE_PATH) as f:
            cache = json.load(f)
            
        # Validiere Cache-Format
        if not isinstance(cache, dict):
            print(f"Warnung: Cache-Datei hat ungültiges Format, erstelle neuen Cache")
            return {}
            
        # Validiere Cache-Einträge
        valid_cache = {}
        for path, metadata in cache.items():
            if isinstance(metadata, dict):
                valid_cache[path] = metadata
                
        return valid_cache
    except Exception as e:
        print(f"Fehler beim Lesen des Caches: {e}, erstelle neuen Cache")
        return {}


def write_cache(cache: Dict[str, Dict]):
    """
    Schreibt den Modell-Metadaten-Cache in die Cache-Datei.
    
    Args:
        cache (Dict[str, Dict]): Der zu speichernde Cache
    """
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Fehler beim Schreiben des Caches: {e}")


def validate_cache_entry(path: Path, cache: Dict[str, Dict]) -> bool:
    """
    Validiert einen Cache-Eintrag für einen Modellpfad.
    
    Diese Funktion prüft, ob der Cache-Eintrag für den angegebenen Pfad
    gültig ist, indem sie die Datei-Metadaten (Größe, Änderungsdatum) vergleicht.
    
    Args:
        path (Path): Der zu validierende Modellpfad
        cache (Dict[str, Dict]): Der Cache
        
    Returns:
        bool: True, wenn der Cache-Eintrag gültig ist, sonst False
    """
    path_str = str(path)
    
    # Prüfe, ob der Pfad im Cache existiert
    if path_str not in cache:
        return False
        
    try:
        # Hole aktuelle Datei-Metadaten
        stat = path.stat()
        size = stat.st_size
        mtime = stat.st_mtime
        
        # Prüfe, ob Metadaten im Cache gespeichert sind
        if "_file_meta" not in cache[path_str]:
            # Füge Metadaten hinzu und betrachte den Eintrag als gültig
            cache[path_str]["_file_meta"] = {
                "size": size,
                "mtime": mtime
            }
            return True
            
        # Vergleiche Metadaten
        cached_meta = cache[path_str]["_file_meta"]
        if (cached_meta.get("size") == size and 
            cached_meta.get("mtime") == mtime):
            return True
            
        # Metadaten haben sich geändert, Eintrag ist ungültig
        return False
    except Exception:
        # Bei Fehlern Eintrag als ungültig betrachten
        return False


def get_or_parse_model_metadata(path: Path, cache: Dict[str, Dict]) -> Dict:
    """
    Holt Modell-Metadaten aus dem Cache oder parst sie aus der Modelldatei.
    
    Diese Funktion versucht, die Metadaten für ein Modell aus dem Cache zu holen.
    Wenn der Cache-Eintrag nicht existiert oder ungültig ist, werden die Metadaten
    aus der Modelldatei geparst und im Cache gespeichert.
    
    Args:
        path (Path): Der Pfad zur Modelldatei
        cache (Dict[str, Dict]): Der Cache
        
    Returns:
        Dict: Die Modell-Metadaten
    """
    path_str = str(path)
    
    # Prüfe, ob der Pfad im Cache existiert und der Eintrag gültig ist
    if path_str in cache and validate_cache_entry(path, cache):
        return cache[path_str]
        
    # Parse Metadaten aus der Modelldatei
    meta = parse_gguf_header(path)
    
    # Füge Datei-Metadaten hinzu
    try:
        stat = path.stat()
        meta["_file_meta"] = {
            "size": stat.st_size,
            "mtime": stat.st_mtime
        }
    except Exception:
        # Bei Fehlern keine Metadaten hinzufügen
        pass
        
    # Speichere im Cache
    cache[path_str] = meta
    return meta
