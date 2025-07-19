"""
/chatbot/yaml_persona_manager.py
Version: 1.0.0
------------------------------
YAML-basierter Persona-Manager für NavyYard

Dieses Modul implementiert einen erweiterten Persona-Manager, der YAML-Dateien
für detaillierte Persona-Definitionen verwendet. Es ermöglicht die Definition
von komplexen Persona-Eigenschaften wie Ton, Stil, Vorlieben und Verhalten.

Der YAML-Persona-Manager ist eine Erweiterung des bestehenden PersonaManager
und kann als Drop-in-Ersatz verwendet werden.

Autor: NavyYard Team
Stand: Juli 2025
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from .error_handler import PersonaError, safe_file_operation
from .persona_manager import PersonaManager

# Logger für dieses Modul
logger = logging.getLogger("YAMLPersonaManager")

class YAMLPersona:
    """
    Repräsentiert eine Persona, die aus einer YAML-Datei geladen wurde.
    
    Diese Klasse speichert alle Eigenschaften einer Persona, wie sie in der
    YAML-Datei definiert sind, und bietet Methoden zum Zugriff auf diese
    Eigenschaften.
    """
    def __init__(self, name: str, data: Dict[str, Any]):
        """
        Initialisiert eine neue YAML-Persona.
        
        Args:
            name (str): Der Name der Persona
            data (Dict[str, Any]): Die aus der YAML-Datei geladenen Daten
        """
        self.name = name
        self.data = data
        self.description = data.get('description', '')
        self.base_prompt = data.get('base_prompt', f"Du bist {name}, ein KI-Assistent.")
        
        # Strukturierte demografische Daten
        self.demographics = data.get('demographics', {})
        self.relationship = data.get('relationship', {})
        
        # Standardwerte für fehlende Felder
        self.personality = data.get('personality', {})
        self.style = data.get('style', {})
        self.preferences = data.get('preferences', {})
        self.behavior = data.get('behavior', {})
        self.constraints = data.get('constraints', {})
        self.voice = data.get('voice', {})
        self.model_params = data.get('model_params', {})
        
    def get_full_prompt(self) -> str:
        """
        Erstellt einen vollständigen Prompt basierend auf allen Persona-Eigenschaften.
        
        Returns:
            str: Der vollständige Prompt für das Sprachmodell
        """
        prompt_parts = [self.base_prompt]
        
        # Persönlichkeit
        if self.personality:
            tone = self.personality.get('tone')
            if tone:
                prompt_parts.append(f"Dein Tonfall ist {tone}.")
                
            formality = self.personality.get('formality')
            if formality:
                if formality == 'formal':
                    prompt_parts.append("Du sprichst formell und höflich.")
                elif formality == 'casual':
                    prompt_parts.append("Du sprichst locker und informell.")
                elif formality == 'very_casual':
                    prompt_parts.append("Du sprichst sehr locker, verwendest Umgangssprache.")
            
            humor = self.personality.get('humor')
            if humor:
                if humor == 'high':
                    prompt_parts.append("Du hast einen ausgeprägten Sinn für Humor und machst gerne Witze.")
                elif humor == 'medium':
                    prompt_parts.append("Du verwendest gelegentlich Humor in deinen Antworten.")
                elif humor == 'low':
                    prompt_parts.append("Du bist eher sachlich und verzichtest meist auf Humor.")
        
        # Stil
        if self.style:
            language = self.style.get('language')
            if language:
                prompt_parts.append(f"Du antwortest auf {language}.")
                
            emoji_usage = self.style.get('emoji_usage')
            if emoji_usage:
                if emoji_usage == 'high':
                    prompt_parts.append("Du verwendest häufig Emojis in deinen Antworten.")
                elif emoji_usage == 'medium':
                    prompt_parts.append("Du verwendest gelegentlich passende Emojis.")
                elif emoji_usage == 'low':
                    prompt_parts.append("Du verwendest selten oder keine Emojis.")
                    
            sentence_length = self.style.get('sentence_length')
            if sentence_length:
                if sentence_length == 'short':
                    prompt_parts.append("Du bevorzugst kurze, prägnante Sätze.")
                elif sentence_length == 'medium':
                    prompt_parts.append("Du verwendest eine ausgewogene Satzlänge.")
                elif sentence_length == 'long':
                    prompt_parts.append("Du drückst dich ausführlich mit längeren Sätzen aus.")
                    
            technical_level = self.style.get('technical_level')
            if technical_level:
                if technical_level == 'high':
                    prompt_parts.append("Du verwendest Fachbegriffe und technische Ausdrücke.")
                elif technical_level == 'medium':
                    prompt_parts.append("Du erklärst technische Konzepte verständlich.")
                elif technical_level == 'low':
                    prompt_parts.append("Du vermeidest Fachbegriffe und erklärst alles einfach.")
        
        # Vorlieben
        if self.preferences:
            likes = self.preferences.get('likes', [])
            if likes:
                prompt_parts.append(f"Du magst: {', '.join(likes)}.")
                
            dislikes = self.preferences.get('dislikes', [])
            if dislikes:
                prompt_parts.append(f"Du magst nicht: {', '.join(dislikes)}.")
        
        # Einschränkungen
        if self.constraints:
            gendering = self.constraints.get('gendering')
            if gendering is not None:
                if not gendering:
                    prompt_parts.append("Du genderst nicht in deinen Antworten.")
                else:
                    prompt_parts.append("Du achtest auf gendergerechte Sprache.")
                    
            political_topics = self.constraints.get('political_topics')
            if political_topics:
                if political_topics == 'avoid':
                    prompt_parts.append("Du vermeidest politische Themen.")
                elif political_topics == 'neutral':
                    prompt_parts.append("Du bleibst bei politischen Themen neutral.")
                    
            max_response_length = self.constraints.get('max_response_length')
            if max_response_length:
                if max_response_length == 'short':
                    prompt_parts.append("Deine Antworten sind kurz und prägnant.")
                elif max_response_length == 'medium':
                    prompt_parts.append("Deine Antworten sind von mittlerer Länge.")
                elif max_response_length == 'long':
                    prompt_parts.append("Deine Antworten sind ausführlich und detailliert.")
        
        return "\n".join(prompt_parts)
    
    def get_behavior(self, key: str, default: str = "") -> str:
        """
        Gibt einen bestimmten Verhaltenstext zurück.
        
        Args:
            key (str): Der Schlüssel des gewünschten Verhaltens
            default (str): Standardwert, falls der Schlüssel nicht existiert
            
        Returns:
            str: Der Verhaltenstext oder der Standardwert
        """
        return self.behavior.get(key, default)


class YAMLPersonaManager(PersonaManager):
    """
    Erweiterter Persona-Manager, der YAML-Dateien für detaillierte Persona-Definitionen verwendet.
    
    Diese Klasse erweitert den bestehenden PersonaManager und fügt Unterstützung
    für YAML-basierte Persona-Definitionen hinzu. Sie kann sowohl mit den alten
    Textdateien als auch mit den neuen YAML-Dateien arbeiten.
    """
    def __init__(self, base_path="config", yaml_path="config/personas", default="abby"):
        """
        Initialisiert den YAMLPersonaManager.
        
        Args:
            base_path (str): Verzeichnis für alte Textdateien
            yaml_path (str): Verzeichnis für YAML-Persona-Dateien
            default (str): Name der Standardpersona
        """
        super().__init__(base_path, default)
        self.yaml_path = yaml_path
        self.current_yaml_persona = None
        
        # Stelle sicher, dass das YAML-Verzeichnis existiert
        os.makedirs(self.yaml_path, exist_ok=True)
        
        # Versuche, die Standardpersona als YAML zu laden
        try:
            self.load_yaml_persona(default)
        except Exception as e:
            logger.warning(f"Konnte YAML-Persona '{default}' nicht laden: {e}")
            logger.info("Verwende stattdessen Text-Persona")
            # Fallback auf die Textdatei-Persona (wird bereits im Super-Konstruktor geladen)
    
    @safe_file_operation
    def load_yaml_persona(self, name: str) -> Optional[YAMLPersona]:
        """
        Lädt eine Persona aus einer YAML-Datei.
        
        Args:
            name (str): Name der zu ladenden Persona (ohne Dateierweiterung)
            
        Returns:
            Optional[YAMLPersona]: Die geladene Persona oder None bei Fehler
            
        Raises:
            PersonaError: Bei Problemen mit der Persona-Datei
        """
        # Sanitize input to prevent directory traversal
        name = os.path.basename(name)
        yaml_path = os.path.join(self.yaml_path, f"{name}.yaml")
        
        if not os.path.exists(yaml_path):
            logger.info(f"Keine YAML-Persona-Datei gefunden: {yaml_path}")
            # Versuche stattdessen, die Textdatei zu laden
            super().load_persona(name)
            self.current_yaml_persona = None
            return None
            
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                raise PersonaError(f"Leere oder ungültige YAML-Datei: {yaml_path}")
                
            # Erstelle die YAML-Persona
            persona = YAMLPersona(name, data)
            
            # Aktualisiere den Persona-Text für die Basisklasse
            self.persona = persona.get_full_prompt()
            self.current_name = name
            self.current_yaml_persona = persona
            
            logger.info(f"YAML-Persona '{name}' erfolgreich geladen")
            return persona
            
        except yaml.YAMLError as e:
            logger.error(f"Fehler beim Parsen der YAML-Datei {yaml_path}: {e}")
            raise PersonaError(f"Fehler beim Parsen der YAML-Datei: {e}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Laden der YAML-Persona {name}: {e}")
            raise PersonaError(f"Fehler beim Laden der YAML-Persona: {e}")
    
    def load_persona(self, name: str) -> str:
        """
        Lädt eine Persona (versucht zuerst YAML, dann Text).
        
        Diese Methode überschreibt die load_persona-Methode der Basisklasse und
        versucht zuerst, eine YAML-Persona zu laden. Wenn das fehlschlägt,
        wird auf die Textdatei zurückgegriffen.
        
        Args:
            name (str): Name der zu ladenden Persona (ohne Dateierweiterung)
            
        Returns:
            str: Der Inhalt der Persona-Datei oder ein Standardtext bei Fehler
        """
        try:
            # Versuche zuerst, die YAML-Persona zu laden
            yaml_persona = self.load_yaml_persona(name)
            if yaml_persona:
                # Wende persona-spezifische Modellparameter an, falls vorhanden
                self.apply_model_params()
                return self.persona
        except Exception as e:
            logger.warning(f"Fehler beim Laden der YAML-Persona '{name}': {e}")
            logger.info("Versuche stattdessen, die Text-Persona zu laden")
            
        # Wenn die YAML-Persona nicht geladen werden konnte, verwende die Textdatei
        return super().load_persona(name)
    
    def get_persona(self) -> str:
        """
        Gibt den Text der aktuell geladenen Persona zurück.
        
        Returns:
            str: Der Inhalt der aktuellen Persona-Datei
        """
        return self.persona
    
    def get_current_name(self) -> str:
        """
        Gibt den Namen der aktuell geladenen Persona zurück.
        
        Returns:
            str: Der Name der aktuellen Persona
        """
        return self.current_name
    
    def get_yaml_persona(self) -> Optional[YAMLPersona]:
        """
        Gibt die aktuell geladene YAML-Persona zurück.
        
        Returns:
            Optional[YAMLPersona]: Die aktuelle YAML-Persona oder None, wenn keine geladen ist
        """
        return self.current_yaml_persona
        
    def apply_model_params(self):
        """
        Wendet persona-spezifische Modellparameter an, falls vorhanden.
        
        Diese Methode prüft, ob die aktuelle YAML-Persona spezifische Modellparameter
        definiert hat, und wendet diese auf das Modell an, ohne es neu zu laden.
        """
        if not self.current_yaml_persona or not hasattr(self.current_yaml_persona, 'model_params'):
            return
            
        model_params = self.current_yaml_persona.model_params
        if not model_params:
            return
            
        # Suche nach einer Referenz auf den Bot
        import sys
        bot = None
        for module_name, module in sys.modules.items():
            if hasattr(module, 'abby_ref') and module.abby_ref is not None:
                bot = module.abby_ref
                break
                
        if not bot or not hasattr(bot, 'model'):
            logger.warning("Konnte keine Bot-Referenz finden, Modellparameter werden nicht angewendet")
            return
            
        # Wende Modellparameter an
        try:
            # Temperatur
            if 'temperature' in model_params and hasattr(bot.model, 'temperature'):
                temp = float(model_params['temperature'])
                if 0.0 <= temp <= 1.0:
                    bot.model.temperature = temp
                    logger.info(f"Persona-spezifische Temperatur gesetzt: {temp}")
                else:
                    logger.warning(f"Ungültige Temperatur in Persona-Konfiguration: {temp}")
                    
            # Weitere Parameter können hier hinzugefügt werden
            
            logger.info(f"Persona-spezifische Modellparameter für '{self.current_name}' angewendet")
        except Exception as e:
            logger.error(f"Fehler beim Anwenden der Persona-spezifischen Modellparameter: {e}")
    
    def list_available_personas(self) -> List[str]:
        """
        Listet alle verfügbaren Personas auf (YAML und Text).
        
        Returns:
            List[str]: Liste der Namen aller verfügbaren Personas
        """
        personas = set()
        
        # Suche nach Textdateien
        if os.path.exists(self.base_path):
            for file in os.listdir(self.base_path):
                if file.endswith('.txt'):
                    personas.add(file[:-4])  # Entferne .txt
        
        # Suche nach YAML-Dateien
        if os.path.exists(self.yaml_path):
            for file in os.listdir(self.yaml_path):
                if file.endswith('.yaml'):
                    personas.add(file[:-5])  # Entferne .yaml
        
        return sorted(list(personas))