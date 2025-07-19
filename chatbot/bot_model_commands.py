"""
/chatbot/bot_model_commands.py
Version: 1.2.0
------------------------------
Erweiterung: RAM-Schätzung in !model info

Dieses Modul implementiert die Modell-bezogenen Befehle für den Chatbot.
Es ermöglicht das Auflisten, Auswählen und Wechseln zwischen verschiedenen
Sprachmodellen zur Laufzeit.

Die Hauptfunktionen sind:
- Auflisten verfügbarer Modelle (!models)
- Auswählen eines Modells nach Index (!model <n>)
- Laden des zuletzt verwendeten Modells (!model last_model)
- Anzeigen von Informationen zum aktuellen Modell (!model)

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

from .model_manager import scan_models, get_model_by_index, load_last_model, save_last_model
from .commands.model_list_command import format_model_list
from .utils.ram_estimator import format_ram_info
from .error_handler import CommandError, log_error
from typing import Optional
import logging

# Logger für dieses Modul
logger = logging.getLogger("ModelCommands")

active_model = None
model_list = []
abby_ref = None


def bind_abby(bot):
    """
    Bindet eine Instanz des AbbyBot an dieses Modul.
    
    Diese Funktion speichert eine Referenz auf die Bot-Instanz, damit die
    Modell-Befehle auf den ModelWrapper zugreifen können.
    
    Args:
        bot: Eine Instanz des AbbyBot
    """
    global abby_ref
    try:
        if bot is None:
            logger.warning("Versuch, None als Bot-Referenz zu binden")
            return
            
        # Prüfe, ob das Bot-Objekt einen ModelWrapper hat
        if not hasattr(bot, "model"):
            logger.error("Bot-Objekt hat kein 'model'-Attribut")
            return
            
        abby_ref = bot
        logger.debug("Bot-Referenz erfolgreich gebunden")
    except Exception as e:
        logger.error(f"Fehler beim Binden der Bot-Referenz: {e}")
        # Keine Exception werfen, da dies beim Startup passiert


def handle_models_command(verbose: bool = False) -> str:
    """
    Verarbeitet den !models Befehl und gibt eine formatierte Liste der verfügbaren Modelle zurück.
    
    Args:
        verbose (bool): Ob detaillierte Informationen angezeigt werden sollen
        
    Returns:
        str: Formatierte Liste der verfügbaren Modelle
    """
    global model_list
    try:
        model_list = scan_models()
        if not model_list:
            logger.warning("Keine Modelle gefunden")
            return "\n⚠️ Keine Modelle gefunden. Bitte stelle sicher, dass GGUF-Dateien im 'models'-Verzeichnis liegen."
            
        return format_model_list(model_list, active_index=active_model.index if active_model else None, verbose=verbose)
    except Exception as e:
        error_msg = f"Fehler beim Scannen nach Modellen: {e}"
        logger.error(error_msg, exc_info=True)
        return f"\n❌ {error_msg}"


def handle_model_select(index: int) -> str:
    """
    Verarbeitet den !model <n> Befehl und wechselt zum angegebenen Modell.
    
    Args:
        index (int): Der Index des zu ladenden Modells
        
    Returns:
        str: Statusmeldung über den Erfolg oder Misserfolg des Modellwechsels
    """
    global active_model, model_list
    
    try:
        # Validiere Eingabe
        if not isinstance(index, int):
            logger.error(f"Ungültiger Index-Typ: {type(index)}")
            return f"\n❌ Ungültiger Index: {index}. Muss eine Zahl sein."
            
        # Prüfe, ob Modelle gescannt wurden
        if not model_list:
            logger.debug("Keine Modelle in der Liste, scanne nach Modellen")
            model_list = scan_models()
            
        # Validiere Index-Bereich
        if not model_list:
            return "\n⚠️ Keine Modelle gefunden. Bitte stelle sicher, dass GGUF-Dateien im 'models'-Verzeichnis liegen."
            
        if index < 1 or index > len(model_list):
            logger.warning(f"Ungültiger Modell-Index: {index}, gültig wären 1-{len(model_list)}")
            return f"\n❌ Ungültiger Index: {index}. Gültige Indizes sind 1-{len(model_list)}."
        
        # Hole Modell nach Index
        model = get_model_by_index(index, model_list)
        if not model:
            logger.error(f"Modell mit Index {index} nicht gefunden, obwohl Index im gültigen Bereich")
            return "\n❌ Modell nicht gefunden (interner Fehler)."
            
        # Prüfe Bot-Referenz
        if not abby_ref:
            logger.error("Keine Bot-Referenz vorhanden")
            return "\n⚠️ Kein Bot-Objekt gebunden (interner Fehler)."
            
        # Lade Modell
        logger.info(f"Versuche Modell zu laden: {model.name} ({model.path})")
        if not abby_ref.model.load_model(str(model.path)):
            logger.error(f"Laden von Modell '{model.name}' fehlgeschlagen")
            return f"\n❌ Laden von Modell '{model.name}' fehlgeschlagen. Mögliche Gründe:\n- Nicht genügend RAM\n- Beschädigte Modelldatei\n- Fehlende Berechtigungen"
            
        # Aktualisiere aktives Modell und speichere es
        active_model = model
        try:
            save_last_model(model)
        except Exception as e:
            logger.warning(f"Konnte letztes Modell nicht speichern: {e}")
            # Kein Fehler zurückgeben, da das Modell erfolgreich geladen wurde
        
        # GPU-Einstellungen speichern, falls verfügbar
        if abby_ref and hasattr(abby_ref.model, "save_gpu_settings"):
            try:
                abby_ref.model.save_gpu_settings()
                logger.info("GPU-Einstellungen nach Modellwechsel gespeichert")
            except Exception as e:
                logger.warning(f"Fehler beim Speichern der GPU-Einstellungen: {e}")
        
        # Status-Banner aktualisieren, falls verfügbar
        if abby_ref and hasattr(abby_ref, "status_banner"):
            try:
                abby_ref.status_banner.update()
            except Exception as e:
                logger.warning(f"Fehler beim Aktualisieren des Status-Banners: {e}")
            
        logger.info(f"Modell erfolgreich gewechselt zu: {model.name}")
        return f"\n🔁 Modell gewechselt: {model.name}"
        
    except Exception as e:
        error_msg = f"Fehler beim Modellwechsel: {e}"
        logger.error(error_msg, exc_info=True)
        return f"\n❌ {error_msg}"


def handle_model_last() -> str:
    """
    Verarbeitet den !model last_model Befehl und lädt das zuletzt verwendete Modell.
    
    Returns:
        str: Statusmeldung über den Erfolg oder Misserfolg des Modellwechsels
    """
    global active_model, model_list
    
    try:
        # Prüfe, ob Modelle gescannt wurden
        if not model_list:
            logger.debug("Keine Modelle in der Liste, scanne nach Modellen")
            model_list = scan_models()
            
        # Lade letztes Modell
        last = load_last_model(model_list)
        if not last:
            logger.warning("Kein gespeichertes letztes Modell gefunden")
            return "\n⚠️ Kein gespeichertes Modell gefunden. Verwende !model <n> um ein Modell auszuwählen."
            
        # Prüfe Bot-Referenz
        if not abby_ref:
            logger.error("Keine Bot-Referenz vorhanden")
            return "\n⚠️ Kein Bot-Objekt gebunden (interner Fehler)."
            
        # Prüfe, ob die Modelldatei noch existiert
        if not last.path.exists():
            logger.error(f"Modelldatei existiert nicht mehr: {last.path}")
            return f"\n❌ Modelldatei nicht gefunden: {last.path}"
            
        # Lade Modell
        logger.info(f"Versuche letztes Modell zu laden: {last.name} ({last.path})")
        if not abby_ref.model.load_model(str(last.path)):
            logger.error(f"Laden von gespeichertem Modell '{last.name}' fehlgeschlagen")
            return f"\n❌ Laden von gespeichertem Modell '{last.name}' fehlgeschlagen. Mögliche Gründe:\n- Nicht genügend RAM\n- Beschädigte Modelldatei\n- Fehlende Berechtigungen"
            
        # Aktualisiere aktives Modell
        active_model = last
        
        # GPU-Einstellungen speichern, falls verfügbar
        if abby_ref and hasattr(abby_ref.model, "save_gpu_settings"):
            try:
                abby_ref.model.save_gpu_settings()
                logger.info("GPU-Einstellungen nach Laden des letzten Modells gespeichert")
            except Exception as e:
                logger.warning(f"Fehler beim Speichern der GPU-Einstellungen: {e}")
        
        # Status-Banner aktualisieren, falls verfügbar
        if abby_ref and hasattr(abby_ref, "status_banner"):
            try:
                abby_ref.status_banner.update()
            except Exception as e:
                logger.warning(f"Fehler beim Aktualisieren des Status-Banners: {e}")
                
        logger.info(f"Letztes Modell erfolgreich geladen: {last.name}")
        return f"\n🔁 Letztes Modell geladen: {last.name}"
        
    except Exception as e:
        error_msg = f"Fehler beim Laden des letzten Modells: {e}"
        logger.error(error_msg, exc_info=True)
        return f"\n❌ {error_msg}"


def handle_model_info() -> str:
    """
    Verarbeitet den !model Befehl und zeigt Informationen zum aktuellen Modell an.
    
    Returns:
        str: Formatierte Informationen zum aktuellen Modell oder eine Fehlermeldung
    """
    try:
        if not active_model:
            logger.warning("Kein aktives Modell vorhanden")
            return "\n❌ Kein Modell aktiv. Verwende !model <n> um ein Modell auszuwählen."
            
        info = active_model
        
        # Prüfe, ob die Modelldatei noch existiert
        if not info.path.exists():
            logger.warning(f"Modelldatei existiert nicht mehr: {info.path}")
            return f"\n⚠️ Modell aktiv, aber Datei nicht mehr vorhanden: {info.path}"
        
        # Prüfe Bot-Referenz für Hardware-Informationen
        hardware_info = {}
        if abby_ref and hasattr(abby_ref, "model") and hasattr(abby_ref.model, "get_hardware_info"):
            hardware_info = abby_ref.model.get_hardware_info()
        
        # Sammle Modellinformationen
        parts = [
            f"🧠 Modell: {info.name}",
            f"📁 Pfad: {info.path}",
        ]
        
        # Hardware-Informationen hinzufügen
        if hardware_info:
            mode = hardware_info.get("mode", "UNKNOWN")
            gpu_layers = hardware_info.get("gpu_layers", 0)
            
            if mode == "GPU":
                parts.append(f"💻 Hardware: GPU ({gpu_layers} Layer)")
            else:
                parts.append(f"💻 Hardware: {mode}")
        
        if info.architecture:
            parts.append(f"🧬 Architektur: {info.architecture}")
        
        if info.context_length:
            parts.append(f"📦 Kontext: {info.context_length} Tokens")
        
        if info.quantization:
            parts.append(f"⚙️ Quantisierung: {info.quantization}")
            try:
                ram_info = format_ram_info(info.quantization, info.context_length or 4096)
                parts.append(f"🧮 RAM-Bedarf: {ram_info}")
            except Exception as e:
                logger.warning(f"Fehler bei der RAM-Berechnung: {e}")
                parts.append("🧮 RAM-Bedarf: Nicht verfügbar")
        
        return "\n" + "\n".join(parts)
        
    except Exception as e:
        error_msg = f"Fehler beim Abrufen der Modellinformationen: {e}"
        logger.error(error_msg, exc_info=True)
        return f"\n❌ {error_msg}"
