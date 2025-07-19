# abby_chatbot/chatbot/persona_manager.py
"""
PersonaManager für Abby Chatbot
Lädt und verwaltet Personas aus dem config-Verzeichnis

Dieses Modul ist verantwortlich für das Laden und Verwalten verschiedener
Chatbot-Personas. Eine Persona definiert den Charakter, Ton und Stil des
Chatbots und wird aus einer Textdatei geladen.

Der PersonaManager ermöglicht es dem Benutzer, zur Laufzeit zwischen
verschiedenen Personas zu wechseln, ohne den Bot neu starten zu müssen.
Jede Persona wird als Textdatei im config-Verzeichnis gespeichert und
enthält Anweisungen für das Sprachmodell.
"""
import os
import logging
from chatbot.error_handler import PersonaError, safe_file_operation

# Logger für dieses Modul
logger = logging.getLogger("PersonaManager")

class PersonaManager:
    """
    Verwaltet die verschiedenen Personas des Chatbots.
    
    Diese Klasse ist verantwortlich für das Laden und Wechseln zwischen
    verschiedenen Chatbot-Personas. Jede Persona wird aus einer Textdatei
    im konfigurierten Verzeichnis geladen und definiert den Charakter und
    Stil des Chatbots.
    """
    def __init__(self, base_path="config", default="abby"):
        """
        Initialisiert den PersonaManager mit einem Basispfad und einer Standardpersona.
        
        Args:
            base_path (str): Verzeichnis, in dem die Persona-Dateien gespeichert sind
            default (str): Name der Standardpersona, die beim Start geladen wird
        """
        self.base_path = base_path
        self.current_name = default
        self.persona = self.load_persona(default)

    @safe_file_operation
    def load_persona(self, name):
        """
        Lädt eine Persona aus einer Textdatei.
        
        Diese Methode versucht, eine Persona mit dem angegebenen Namen aus dem
        konfigurierten Verzeichnis zu laden. Wenn die Datei nicht gefunden wird,
        wird eine neutrale Standardpersona verwendet.
        
        Args:
            name (str): Name der zu ladenden Persona (ohne Dateierweiterung)
            
        Returns:
            str: Der Inhalt der Persona-Datei oder ein Standardtext bei Fehler
            
        Raises:
            PersonaError: Bei Problemen mit der Persona-Datei (außer FileNotFoundError)
        """
        if not name or not isinstance(name, str):
            logger.warning(f"Ungültiger Persona-Name: {name}, verwende 'neutral'")
            self.persona = "Du bist ein neutraler Assistent."
            self.current_name = "neutral"
            return self.persona
            
        # Sanitize input to prevent directory traversal
        name = os.path.basename(name)
        pfad = os.path.join(self.base_path, f"{name}.txt")
        
        try:
            if not os.path.exists(pfad):
                logger.warning(f"Persona-Datei nicht gefunden: {pfad}")
                self.persona = "Du bist ein neutraler Assistent."
                self.current_name = "neutral"
                return self.persona
                
            with open(pfad, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            if not content:
                logger.warning(f"Leere Persona-Datei: {pfad}")
                self.persona = "Du bist ein neutraler Assistent."
                self.current_name = "neutral"
                return self.persona
                
            self.persona = content
            self.current_name = name
            logger.info(f"Persona '{name}' erfolgreich geladen")
            return self.persona
            
        except FileNotFoundError:
            logger.warning(f"Persona-Datei nicht gefunden: {pfad}")
            self.persona = "Du bist ein neutraler Assistent."
            self.current_name = "neutral"
            return self.persona
        except UnicodeDecodeError as e:
            logger.error(f"Fehler beim Dekodieren der Persona-Datei {pfad}: {e}")
            raise PersonaError(f"Fehler beim Lesen der Persona-Datei: {e}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Laden der Persona {name}: {e}")
            raise PersonaError(f"Fehler beim Laden der Persona: {e}")

    def get_persona(self):
        """
        Gibt den Text der aktuell geladenen Persona zurück.
        
        Returns:
            str: Der Inhalt der aktuellen Persona-Datei
        """
        return self.persona

    def get_current_name(self):
        """
        Gibt den Namen der aktuell geladenen Persona zurück.
        
        Returns:
            str: Der Name der aktuellen Persona
        """
        return self.current_name
