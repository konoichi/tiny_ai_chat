"""
/chatbot/commands/model_list_command.py
Version: 1.0.0
------------------------------
Erzeugt die Ausgabe für den Chat-Befehl `!models`.

Funktionen:
- Listet alle Modelle mit Nummerierung
- Hebt das aktuell aktive Modell hervor
- Optional: zeigt Metadaten (Kontext, Architektur, Quantisierung)

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

from ..model_manager import ModelInfo
from typing import List, Optional


def format_model_list(models: List[ModelInfo], active_index: Optional[int] = None, verbose: bool = False) -> str:
    if not models:
        return "\n❌ Keine Modelle gefunden. Stelle sicher, dass sich .gguf-Dateien im /models Verzeichnis befinden."

    lines = ["\n📂 Verfügbare Modelle:"]
    for model in models:
        prefix = f"[*{model.index}*]" if model.index == active_index else f"[{model.index}]"
        line = f"{prefix} {model.name}"
        if verbose:
            details = []
            if model.architecture:
                details.append(f"Arch: {model.architecture}")
            if model.context_length:
                details.append(f"Ctx: {model.context_length}")
            if model.quantization:
                details.append(f"Q: {model.quantization}")
            if details:
                line += "  (" + ", ".join(details) + ")"
        lines.append(line)
    return "\n".join(lines)
