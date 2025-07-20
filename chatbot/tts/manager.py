# /chatbot/tts/manager.py
"""
Version: 5.0.0
------------------------------
ID: NAVYYARD-REFACTOR-V5-TTS-TEXT-CHUNKING-01
Beschreibung: Manager für die Text-to-Speech-Funktionalität.
FEATURE: Implementiert intelligentes Text-Chunking. Lange Texte, die
das Limit des TTS-Servers überschreiten, werden jetzt automatisch an
Satzgrenzen in kleinere Stücke zerlegt. Diese Stücke werden dann
nacheinander abgespielt, was eine nahtlose Sprachausgabe für beliebig
lange Antworten ermöglicht.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
import logging
import requests
import io
import json
import time

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
        # Lese das Zeichenlimit für Chunks aus der Config, mit einem sicheren Standardwert.
        self.max_chars = config.get("max_chars", 450)

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

    def _split_text(self, text: str):
        """
        Teilt einen langen Text in sinnvolle Stücke, die das max_chars-Limit nicht überschreiten.
        """
        chunks = []
        remaining_text = text.strip()
        
        while len(remaining_text) > self.max_chars:
            # Finde die letzte mögliche Trennstelle (Satzende) innerhalb des Limits.
            split_pos = -1
            for punctuation in ['.', '!', '?', '\n', ';', ':']:
                pos = remaining_text.rfind(punctuation, 0, self.max_chars)
                if pos > split_pos:
                    split_pos = pos
            
            # Wenn kein Satzende gefunden wurde, suche nach dem letzten Komma oder Leerzeichen.
            if split_pos == -1:
                for punctuation in [',', ' ']:
                    pos = remaining_text.rfind(punctuation, 0, self.max_chars)
                    if pos > split_pos:
                        split_pos = pos

            # Wenn immer noch keine Trennstelle gefunden wurde, mache einen harten Schnitt.
            if split_pos == -1:
                split_pos = self.max_chars - 1

            # Füge den Chunk zur Liste hinzu und bereite den restlichen Text vor.
            chunks.append(remaining_text[:split_pos + 1])
            remaining_text = remaining_text[split_pos + 1:].lstrip()
            
        # Füge den letzten verbleibenden Teil des Textes hinzu.
        if remaining_text:
            chunks.append(remaining_text)
            
        return chunks

    def synthesize(self, text: str) -> bytes:
        """
        Sendet Text an den TTS-Server und empfängt die WAV-Audiodaten.
        """
        if not self.is_configured:
            return None
        try:
            payload = {"text": text}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.server_url, data=json.dumps(payload), headers=headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Fehler bei der Verbindung zum TTS-Server: {e}")
            return None

    def speak(self, text: str):
        """
        Nimmt einen potenziell langen Text, teilt ihn in Stücke und spielt diese nacheinander ab.
        """
        if not self.enabled or not text or not text.strip():
            return
            
        if not pygame.mixer.get_init():
            self.logger.error("Pygame-Mixer ist nicht initialisiert. Kann Audio nicht abspielen.")
            return

        # Zerlege den Text in abspielbare Stücke.
        text_chunks = self._split_text(text)
        self.logger.info(f"Text wurde in {len(text_chunks)} Audio-Stücke aufgeteilt.")

        for i, chunk in enumerate(text_chunks):
            # Warte, bis der vorherige Sound fertig ist.
            while pygame.mixer.get_busy():
                time.sleep(0.1)

            self.logger.info(f"Spiele Stück {i+1}/{len(text_chunks)} ab: '{chunk[:80]}...'")
            audio_data = self.synthesize(chunk)
            
            if not audio_data:
                self.logger.error(f"Audio-Synthese für Stück {i+1} fehlgeschlagen.")
                continue

            try:
                sound = pygame.mixer.Sound(io.BytesIO(audio_data))
                sound.play()
            except Exception as e:
                self.logger.error(f"Ein Fehler ist bei der Pygame-Wiedergabe aufgetreten: {e}")
                # Breche bei einem Wiedergabefehler ab, um eine Endlosschleife zu vermeiden.
                break
