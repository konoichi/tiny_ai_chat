# /chatbot/config_handler.py
"""
Verwaltet das Lesen und Schreiben der Konfigurationsdatei (settings.yaml).
Abstrahiert die Dateizugriffe für den ModelWrapper.
"""
import yaml
import os
import logging
from chatbot.error_handler import ConfigError, safe_file_operation

logger = logging.getLogger("ConfigHandler")

class ConfigManager:
    def __init__(self, config_path="config/settings.yaml"):
        self.config_path = config_path

    @safe_file_operation
    def load_model_config(self) -> dict:
        """Lädt die Modell-spezifische Konfiguration aus der YAML-Datei."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Konfigurationsdatei fehlt: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if not config or "model" not in config:
                raise ConfigError("Keine 'model'-Sektion in der Konfiguration gefunden.")
            
            return config.get("model", {})
        except yaml.YAMLError as e:
            raise ConfigError(f"Fehler beim Parsen der YAML-Datei: {e}")

    @safe_file_operation
    def save_gpu_settings(self, gpu_layers: int) -> bool:
        """Speichert die Anzahl der GPU-Layer in der Konfigurationsdatei."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        
        if "model" not in config:
            config["model"] = {}
            
        config["model"]["gpu_layers"] = gpu_layers
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)
            
        logger.info(f"GPU-Einstellungen gespeichert: gpu_layers={gpu_layers}")
        return True