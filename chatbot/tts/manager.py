# /chatbot/tts/manager.py
"""
Version: 4.0.2
------------------------------
ID: NAVYYARD-REFACTOR-V4-TTS-PYGAME-JSON-FIX-01
Beschreibung: Manager für die Text-to-Speech-Funktionalität.
FIX: Die 'synthesize'-Methode wurde geändert, um den JSON-Payload
und die Header manuell zu erstellen, anstatt sich auf die Automatik
der 'requests'-Bibliothek zu verlassen. Dies ist ein gezielter Versuch,
ein vermutetes Problem bei der Datenübertragung an den Server zu beheben,
das das "Geisterwort"-Problem verursacht.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
import logging
import requests
import io
import json # Importiere das json-Modul

# Pygame wird jetzt für die Audio-Wiedergabe verwendet.
import pygame

class TTSManager:
    def __init__(self, config):
        """
        Initialisiert den TTS-Manager und die Pygame-Audio-Engine.
        """
        self.logger = logging.getLogger("TTSManager")
        self.server_url = config.get("server_url")
        self.enabled = config.get("enabled", False) and bool(self.server_url)
        self.is_configured = bool(self.server_url)

        if self.is_configured:
            try:
                pygame.mixer.init(frequency=44100, buffer=2048)
                self.logger.info("Pygame-Mixer erfolgreich initialisiert.")
            except Exception as e:
                self.logger.error(f"Fehler bei der Initialisierung von Pygame-Mixer: {e}")
                self.is_configured = False

    def enable(self):
        """Aktiviert TTS zur Laufzeit."""
        if self.is_configured:
            self.enabled = True
            self.logger.info("TTS zur Laufzeit aktiviert.")
        else:
            self.logger.warning("TTS kann nicht aktiviert werden (nicht konfiguriert oder Mixer-Fehler).")

    def disable(self):
        """Deaktiviert TTS zur Laufzeit."""
        self.enabled = False
        self.logger.info("TTS zur Laufzeit deaktiviert.")

    def is_enabled(self):
        """Prüft, ob TTS aktuell aktiviert ist."""
        return self.enabled

    def synthesize(self, text: str) -> bytes:
        """
        Sendet Text an den TTS-Server und empfängt die WAV-Audiodaten.
        Jetzt mit expliziter JSON-Erstellung.
        """
        if not self.is_configured:
            return None
        try:
            # *** DIE ÄNDERUNG ***
            # Wir erstellen den Payload als Dictionary...
            payload = {"text": text}
            # ...und die Header, um sicherzustellen, dass der Server weiß, dass es JSON ist.
            headers = {'Content-Type': 'application/json'}
            
            # Wir übergeben die Daten jetzt als manuell erstellten JSON-String.
            response = requests.post(self.server_url, data=json.dumps(payload), headers=headers)
            
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Fehler bei der Verbindung zum TTS-Server: {e}")
            return None

    def speak(self, text: str):
        """
        Synthetisiert Text und spielt ihn direkt über den Pygame-Mixer ab.
        """
        self.logger.info(f"TTS 'speak' aufgerufen mit Text: '{text}'")

        if not self.enabled or not text:
            return
            
        if not pygame.mixer.get_init():
            self.logger.error("Pygame-Mixer ist nicht initialisiert. Kann Audio nicht abspielen.")
            return

        if pygame.mixer.get_busy():
            self.logger.warning("TTS-Anfrage ignoriert, da bereits Audio abgespielt wird.")
            return

        audio_data = self.synthesize(text)
        if not audio_data:
            self.logger.error("Audio-Synthese fehlgeschlagen, keine Daten zum Abspielen.")
            return

        try:
            sound = pygame.mixer.Sound(io.BytesIO(audio_data))
            sound.play()
        except Exception as e:
            self.logger.error(f"Ein Fehler ist bei der Pygame-Wiedergabe aufgetreten: {e}")

