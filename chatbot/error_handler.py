"""
/chatbot/error_handler.py
Version: 1.0.0
------------------------------
Zentrales Fehlerbehandlungsmodul für den NavyYard Chatbot

Dieses Modul stellt zentrale Funktionen und Klassen für die Fehlerbehandlung
im gesamten Chatbot-System bereit. Es bietet:
- Benutzerdefinierte Ausnahmen für verschiedene Fehlertypen
- Hilfsfunktionen für einheitliche Fehlerbehandlung und -protokollierung
- Dekoratoren für einfache Fehlerbehandlung in anderen Modulen

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

import logging
import sys
import traceback
from functools import wraps
from colorama import Fore, Style

# Logger für dieses Modul
logger = logging.getLogger("ErrorHandler")

# Benutzerdefinierte Ausnahmen
class ChatbotError(Exception):
    """Basisklasse für alle Chatbot-spezifischen Ausnahmen."""
    pass

class ModelError(ChatbotError):
    """Fehler bei der Interaktion mit dem Sprachmodell."""
    pass

class ConfigError(ChatbotError):
    """Fehler in der Konfiguration."""
    pass

class PersonaError(ChatbotError):
    """Fehler beim Laden oder Verwalten von Personas."""
    pass

class CommandError(ChatbotError):
    """Fehler bei der Verarbeitung von Befehlen."""
    pass

# Hilfsfunktionen für die Fehlerbehandlung
def log_error(error, level=logging.ERROR, show_traceback=False):
    """
    Protokolliert einen Fehler mit optionalem Stacktrace.
    
    Args:
        error (Exception): Die aufgetretene Ausnahme
        level (int): Logging-Level (default: ERROR)
        show_traceback (bool): Ob der Stacktrace protokolliert werden soll
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if show_traceback:
        tb = traceback.format_exc()
        logger.log(level, f"{error_type}: {error_msg}\n{tb}")
    else:
        logger.log(level, f"{error_type}: {error_msg}")

def format_error_for_user(error, verbose=False):
    """
    Formatiert eine Fehlermeldung für die Ausgabe an den Benutzer.
    
    Args:
        error (Exception): Die aufgetretene Ausnahme
        verbose (bool): Ob detaillierte Informationen angezeigt werden sollen
        
    Returns:
        str: Formatierte Fehlermeldung
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if isinstance(error, ChatbotError):
        # Für benutzerdefinierte Ausnahmen spezifischere Meldungen
        if isinstance(error, ModelError):
            prefix = "❌ Modellfehler"
        elif isinstance(error, ConfigError):
            prefix = "⚙️ Konfigurationsfehler"
        elif isinstance(error, PersonaError):
            prefix = "👤 Persona-Fehler"
        elif isinstance(error, CommandError):
            prefix = "🔍 Befehlsfehler"
        else:
            prefix = "❌ Fehler"
    else:
        # Für allgemeine Ausnahmen
        prefix = "❌ Systemfehler"
    
    if verbose:
        return f"{prefix}: {error_type} - {error_msg}"
    else:
        return f"{prefix}: {error_msg}"

def handle_errors(func=None, *, show_traceback=False, return_value=None, verbose=False):
    """
    Dekorator für einheitliche Fehlerbehandlung in Funktionen.
    
    Args:
        func: Die zu dekorierende Funktion
        show_traceback (bool): Ob der Stacktrace protokolliert werden soll
        return_value: Rückgabewert im Fehlerfall (None = Fehlermeldung)
        verbose (bool): Ob detaillierte Fehlermeldungen zurückgegeben werden sollen
        
    Returns:
        Dekorierte Funktion mit Fehlerbehandlung
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                log_error(e, show_traceback=show_traceback)
                if return_value is None:
                    return format_error_for_user(e, verbose)
                return return_value
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

def safe_file_operation(operation):
    """
    Dekorator für sichere Dateioperationen mit Fehlerbehandlung.
    
    Args:
        operation: Die zu dekorierende Dateioperation
        
    Returns:
        Dekorierte Funktion mit Fehlerbehandlung für Dateioperationen
    """
    @wraps(operation)
    def wrapper(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except FileNotFoundError as e:
            log_error(e)
            return f"❌ Datei nicht gefunden: {e}"
        except PermissionError as e:
            log_error(e)
            return f"🔒 Keine Berechtigung: {e}"
        except IsADirectoryError as e:
            log_error(e)
            return f"📁 Ist ein Verzeichnis: {e}"
        except Exception as e:
            log_error(e, show_traceback=True)
            return f"❌ Dateifehler: {e}"
    return wrapper