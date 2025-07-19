# chatbot/tts/manager.py
# ID: TTS-MANAGER-SIMPLE-03-FIXED

import requests
import logging
from typing import Optional

logger = logging.getLogger("TTSManager")

class TTSManager:
    """
    Simpler Manager für die Verbindung zum externen Piper TTS-Server.
    Kann zur Laufzeit an- und ausgeschaltet werden.
    """
    def __init__(self, config: dict):
        """
        Initialisiert den TTS-Manager mit der Konfiguration aus settings.yaml.
        """
        self.server_url = config.get('server_url', '').rstrip('/')
        self.default_model = config.get('default_model', 'de_DE-thorsten-high')
        self._session = requests.Session()

        # Prüft, ob der Server überhaupt konfiguriert ist.
        self.is_configured = bool(self.server_url)
        
        # Setzt den Startzustand basierend auf der Konfiguration.
        self.enabled = config.get('enabled', False) and self.is_configured

        if config.get('enabled', False) and not self.is_configured:
            logger.error("TTS ist in der settings.yaml aktiviert, aber es wurde keine server_url angegeben. TTS bleibt deaktiviert.")
            self.enabled = False
    
    def enable(self):
        """Aktiviert TTS zur Laufzeit, wenn eine Server-URL konfiguriert ist."""
        if self.is_configured:
            self.enabled = True
            logger.info("TTS zur Laufzeit aktiviert.")
        else:
            logger.warning("TTS kann nicht aktiviert werden, da keine server_url in der settings.yaml konfiguriert ist.")

    def disable(self):
        """Deaktiviert TTS zur Laufzeit."""
        self.enabled = False
        logger.info("TTS zur Laufzeit deaktiviert.")

    def is_available(self) -> bool:
        """Prüft, ob der TTS-Server erreichbar ist."""
        if not self.enabled or not self.is_configured:
            return False
        try:
            res = self._session.get(f"{self.server_url}/health", timeout=2)
            return res.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def synthesize(self, text: str, model: Optional[str] = None, speaker_id: str = "0") -> Optional[bytes]:
        """Fordert die Audio-Synthese vom Server an."""
        if not self.enabled or not self.is_configured:
            logger.warning("Versuch, TTS zu verwenden, obwohl es deaktiviert/nicht konfiguriert ist.")
            return None

        payload = {
            "text": text,
            "model": model or self.default_model,
            "speaker_id": speaker_id
        }
        
        try:
            res = self._session.post(f"{self.server_url}/tts", json=payload, timeout=15)
            res.raise_for_status()
            return res.content
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS-Synthese fehlgeschlagen: {e}")
            return None
