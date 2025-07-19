"""
/chatbot/model_wrapper.py
Version: 1.2.0
------------------------------
Modell-Wrapper mit dynamischem Modellwechsel (load_model) + Streaming + Hardware-Status

Diese Klasse kapselt die Interaktion mit dem LLM (Large Language Model) über die llama-cpp-Python-Bibliothek.
Sie bietet eine vereinfachte Schnittstelle für:
- Laden von GGUF-Modellen aus Konfiguration oder zur Laufzeit
- Generieren von Chat-Antworten (synchron und als Stream)
- Konfiguration von Modellparametern (Temperatur, Kontext, etc.)
- Fehlerbehandlung bei Modellinteraktionen
- Hardware-Status-Erkennung (CPU/GPU, GPU-Layer)

Erweiterungen:
- neue Methode `load_model(path: str)`
- unterstützt Live-Wechsel des Modells zur Laufzeit
- Hardware-Status-Erkennung und -Reporting
- Zuverlässige GPU-Konfiguration

Bestehende Struktur und Initialverhalten bleiben erhalten.
Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

import yaml
from llama_cpp import Llama
import os
import contextlib
import sys
import logging
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from chatbot.config import SETTINGS
from chatbot.error_handler import ModelError, ConfigError, handle_errors, safe_file_operation

# Logger für dieses Modul
logger = logging.getLogger("ModelWrapper")

class HardwareMode(Enum):
    """Enum für den Hardware-Modus des Modells."""
    CPU = "CPU"
    GPU = "GPU"
    UNKNOWN = "UNKNOWN"

@dataclass
class HardwareStatus:
    """Datenklasse zur Speicherung des Hardware-Status."""
    mode: HardwareMode = HardwareMode.UNKNOWN
    gpu_layers: int = 0
    cuda_available: bool = False
    last_checked: float = 0.0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@contextlib.contextmanager
def suppress_llama_output(suppress=True):
    if suppress:
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                yield
    else:
        yield


class ModelWrapper:
    """
    Wrapper-Klasse für die Interaktion mit dem LLM über llama-cpp-python.
    
    Diese Klasse abstrahiert die direkte Interaktion mit dem Sprachmodell und bietet
    eine vereinfachte Schnittstelle für das Laden von Modellen, die Konfiguration
    von Parametern und die Generierung von Antworten.
    
    Attributes:
        model: Das geladene Llama-Modell
        temperature (float): Die Temperatur für die Textgenerierung
        model_path (str): Pfad zur aktuell geladenen Modelldatei
        hardware_status (HardwareStatus): Status der Hardware (CPU/GPU)
    """
    def __init__(self, config_path="config/settings.yaml"):
        """
        Initialisiert den ModelWrapper und lädt das Modell aus der Konfiguration.
        
        Args:
            config_path (str): Pfad zur YAML-Konfigurationsdatei
        """
        self.model = None
        self.temperature = 0.7
        self.model_path = None
        self.hardware_status = HardwareStatus()
        self.response_cache = {}  # Cache für Antworten
        self.cache_size = 100     # Maximale Anzahl von Cache-Einträgen
        self._check_cuda_availability()
        self.load_from_config(config_path)
        
    def _check_cuda_availability(self):
        """
        Prüft, ob CUDA verfügbar ist.
        
        Diese Methode versucht, die CUDA-Verfügbarkeit zu erkennen, indem sie
        nach relevanten Umgebungsvariablen und Bibliotheken sucht.
        """
        try:
            # Prüfe Umgebungsvariablen
            cuda_available = False
            
            # Prüfe CUDA_VISIBLE_DEVICES
            if "CUDA_VISIBLE_DEVICES" in os.environ and os.environ["CUDA_VISIBLE_DEVICES"] != "-1":
                cuda_available = True
                logger.info("CUDA erkannt über CUDA_VISIBLE_DEVICES")
                
            # Prüfe LLAMA_CUBLAS
            if "LLAMA_CUBLAS" in os.environ and os.environ["LLAMA_CUBLAS"] == "1":
                cuda_available = True
                logger.info("CUDA erkannt über LLAMA_CUBLAS=1")
                
            # Versuche, CUDA-Bibliotheken zu importieren (optional)
            try:
                import ctypes
                ctypes.CDLL("libcudart.so")
                cuda_available = True
                logger.info("CUDA-Bibliothek gefunden")
            except:
                pass
                
            self.hardware_status.cuda_available = cuda_available
            logger.info(f"CUDA-Verfügbarkeit: {cuda_available}")
            
        except Exception as e:
            logger.warning(f"Fehler bei der CUDA-Erkennung: {e}")
            self.hardware_status.cuda_available = False

    @safe_file_operation
    def load_from_config(self, config_path):
        """
        Lädt Modellkonfiguration aus einer YAML-Datei und initialisiert das Modell.
        
        Diese Methode liest die Modellkonfiguration (Pfad, GPU-Layer, Kontext, etc.)
        aus einer YAML-Datei und lädt das Modell entsprechend.
        
        Args:
            config_path (str): Pfad zur YAML-Konfigurationsdatei
            
        Raises:
            FileNotFoundError: Wenn die Konfigurationsdatei nicht gefunden wird
            ConfigError: Bei Problemen mit der Konfiguration
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Konfigurationsdatei fehlt: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
            if not config:
                raise ConfigError("Leere oder ungültige Konfigurationsdatei")
                
            model_cfg = config.get("model", {})
            if not model_cfg:
                logger.warning("Keine Modellkonfiguration gefunden, verwende Standardwerte")

            model_path = model_cfg.get("path", "models/dolphin-2.2.1-mistral-7b.Q4_K_M.gguf")
            n_gpu_layers = model_cfg.get("gpu_layers", 50)
            n_ctx = model_cfg.get("context", 4096)
            chat_format = model_cfg.get("chat_format", "chatml")
            self.temperature = model_cfg.get("temperature", 0.7)
            
            # Neue Inferenz-Parameter laden
            self.top_p = model_cfg.get("top_p", 0.9)
            self.top_k = model_cfg.get("top_k", 40)
            self.repeat_penalty = model_cfg.get("repeat_penalty", 1.1)
            self.n_threads = model_cfg.get("threads", 8)
            
            # Validiere Werte
            if not isinstance(n_gpu_layers, int) or n_gpu_layers < 0:
                logger.warning(f"Ungültiger Wert für GPU-Layer: {n_gpu_layers}, verwende 50")
                n_gpu_layers = 50
                
            if not isinstance(n_ctx, int) or n_ctx < 512:
                logger.warning(f"Ungültiger Kontextwert: {n_ctx}, verwende 4096")
                n_ctx = 4096
                
            if not isinstance(self.temperature, (int, float)) or not 0 <= self.temperature <= 1:
                logger.warning(f"Ungültige Temperatur: {self.temperature}, verwende 0.7")
                self.temperature = 0.7
                
            if not isinstance(self.top_p, (int, float)) or not 0 <= self.top_p <= 1:
                logger.warning(f"Ungültiger top_p-Wert: {self.top_p}, verwende 0.9")
                self.top_p = 0.9
                
            if not isinstance(self.top_k, int) or self.top_k < 0:
                logger.warning(f"Ungültiger top_k-Wert: {self.top_k}, verwende 40")
                self.top_k = 40
                
            if not isinstance(self.repeat_penalty, (int, float)) or self.repeat_penalty < 1:
                logger.warning(f"Ungültiger repeat_penalty-Wert: {self.repeat_penalty}, verwende 1.1")
                self.repeat_penalty = 1.1
                
            if not isinstance(self.n_threads, int) or self.n_threads < 1:
                logger.warning(f"Ungültiger threads-Wert: {self.n_threads}, verwende 8")
                self.n_threads = 8

            return self.load_model(model_path, n_gpu_layers, n_ctx, chat_format)
            
        except yaml.YAMLError as e:
            raise ConfigError(f"Fehler beim Parsen der YAML-Datei: {e}")
        except Exception as e:
            if not isinstance(e, (FileNotFoundError, ConfigError)):
                raise ConfigError(f"Unerwarteter Fehler beim Laden der Konfiguration: {e}")

    def load_model(self, path, n_gpu_layers=50, n_ctx=4096, chat_format="chatml"):
        """
        Ermöglicht dynamisches Laden eines Modells zur Laufzeit.
        
        Diese Methode lädt ein GGUF-Modell mit den angegebenen Parametern.
        Sie kann zur Laufzeit aufgerufen werden, um zwischen verschiedenen
        Modellen zu wechseln, ohne den Bot neu zu starten.
        
        Args:
            path (str): Pfad zur GGUF-Modelldatei
            n_gpu_layers (int): Anzahl der GPU-Layer (0 für CPU-only)
            n_ctx (int): Kontextfenstergröße in Tokens
            chat_format (str): Chat-Format (z.B. "chatml", "llama2")
            
        Returns:
            bool: True bei erfolgreichem Laden, False bei Fehler
        """
        if not os.path.exists(path):
            logger.error(f"Modelldatei nicht gefunden: {path}")
            return False
            
        try:
            # Validiere Parameter
            if not isinstance(n_gpu_layers, int) or n_gpu_layers < 0:
                logger.warning(f"Ungültiger Wert für GPU-Layer: {n_gpu_layers}, verwende 50")
                n_gpu_layers = 50
                
            if not isinstance(n_ctx, int) or n_ctx < 512:
                logger.warning(f"Ungültiger Kontextwert: {n_ctx}, verwende 4096")
                n_ctx = 4096
                
            valid_formats = ["chatml", "llama2", "mistral", "openchat", "simple"]
            if chat_format not in valid_formats:
                logger.warning(f"Unbekanntes Chat-Format: {chat_format}, verwende chatml")
                chat_format = "chatml"
            
            # Stelle sicher, dass GPU-Einstellungen korrekt angewendet werden
            self._ensure_gpu_config()
                
            with suppress_llama_output(not SETTINGS.debug):
                self.model = Llama(
                    model_path=path,
                    n_gpu_layers=n_gpu_layers,
                    n_ctx=n_ctx,
                    chat_format=chat_format,
                    verbose=SETTINGS.debug
                    # n_threads parameter removed as it's no longer supported
                )
            self.model_path = path
            
            # Hardware-Status nach dem Laden aktualisieren
            self._detect_hardware_mode(n_gpu_layers)
            
            # Überprüfe, ob GPU-Beschleunigung wie erwartet funktioniert
            if n_gpu_layers > 0 and self.hardware_status.mode == HardwareMode.CPU:
                warning_msg = (f"⚠️ GPU-Beschleunigung wurde angefordert (Layers: {n_gpu_layers}), "
                              f"aber das Modell läuft im CPU-Modus. Möglicherweise fehlen CUDA-Treiber oder -Bibliotheken.")
                logger.warning(warning_msg)
                
                # Benutzerbenachrichtigung
                from colorama import Fore
                print(Fore.YELLOW + warning_msg)
                print(Fore.YELLOW + "⚠️ Verwende '!hardware' für detaillierte Informationen zur Diagnose.")
                
            logger.info(f"Modell erfolgreich geladen: {path} im {self.hardware_status.mode.value}-Modus")
            if self.hardware_status.mode == HardwareMode.GPU:
                logger.info(f"GPU-Layer: {self.hardware_status.gpu_layers}")
                
            return True
        except FileNotFoundError:
            logger.error(f"Modelldatei nicht gefunden: {path}")
            return False
        except MemoryError:
            logger.error(f"Nicht genügend Arbeitsspeicher zum Laden von {path}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Laden von {path}: {str(e)}", exc_info=SETTINGS.debug)
            return False
            
    def _ensure_gpu_config(self):
        """
        Stellt sicher, dass die GPU-Konfiguration korrekt gesetzt ist.
        
        Diese Methode setzt die notwendigen Umgebungsvariablen für die
        GPU-Beschleunigung, falls CUDA verfügbar ist, und überprüft, ob
        die Konfiguration korrekt angewendet wurde.
        
        Returns:
            bool: True, wenn die GPU-Konfiguration korrekt ist, sonst False
        """
        config_ok = True
        
        if self.hardware_status.cuda_available:
            # Setze LLAMA_CUBLAS, wenn nicht bereits gesetzt
            if "LLAMA_CUBLAS" not in os.environ:
                os.environ["LLAMA_CUBLAS"] = "1"
                logger.info("LLAMA_CUBLAS=1 gesetzt")
            elif os.environ["LLAMA_CUBLAS"] != "1":
                os.environ["LLAMA_CUBLAS"] = "1"
                logger.info("LLAMA_CUBLAS auf 1 geändert")
                
            # Stelle sicher, dass CUDA_VISIBLE_DEVICES nicht auf -1 gesetzt ist
            if "CUDA_VISIBLE_DEVICES" in os.environ and os.environ["CUDA_VISIBLE_DEVICES"] == "-1":
                os.environ["CUDA_VISIBLE_DEVICES"] = "0"
                logger.info("CUDA_VISIBLE_DEVICES von -1 auf 0 geändert")
                
            # Überprüfe, ob die GPU-Konfiguration korrekt ist
            if "LLAMA_CUBLAS" not in os.environ or os.environ["LLAMA_CUBLAS"] != "1":
                logger.warning("LLAMA_CUBLAS ist nicht auf 1 gesetzt, GPU-Beschleunigung könnte nicht funktionieren")
                config_ok = False
                
            if "CUDA_VISIBLE_DEVICES" in os.environ and os.environ["CUDA_VISIBLE_DEVICES"] == "-1":
                logger.warning("CUDA_VISIBLE_DEVICES ist auf -1 gesetzt, GPU-Beschleunigung ist deaktiviert")
                config_ok = False
                
            # Versuche, CUDA-Bibliotheken zu laden, um zu überprüfen, ob sie verfügbar sind
            try:
                import ctypes
                try:
                    ctypes.CDLL("libcudart.so")
                except:
                    try:
                        ctypes.CDLL("cudart64_*.dll")  # Windows
                    except:
                        logger.warning("CUDA-Bibliotheken konnten nicht geladen werden, GPU-Beschleunigung könnte nicht funktionieren")
                        config_ok = False
            except ImportError:
                logger.warning("ctypes-Modul nicht verfügbar, CUDA-Bibliotheken können nicht überprüft werden")
                
            if config_ok:
                logger.info("GPU-Konfiguration erfolgreich überprüft")
            else:
                logger.warning("GPU-Konfiguration könnte Probleme haben, siehe Warnungen oben")
        else:
            logger.info("CUDA nicht verfügbar, keine GPU-Konfiguration gesetzt")
            
        return config_ok
            
    def _detect_hardware_mode(self, requested_gpu_layers=0):
        """
        Erkennt den aktuellen Hardware-Modus (CPU/GPU) des Modells.
        
        Diese Methode analysiert das geladene Modell und bestimmt, ob es
        auf der CPU oder GPU läuft und wie viele GPU-Layer verwendet werden.
        
        Args:
            requested_gpu_layers (int): Die Anzahl der angeforderten GPU-Layer
        """
        import time
        
        # Setze Standardwerte
        self.hardware_status.mode = HardwareMode.UNKNOWN
        self.hardware_status.gpu_layers = 0
        
        try:
            if self.model is None:
                logger.warning("Kein Modell geladen, Hardware-Modus kann nicht erkannt werden")
                return
                
            # Prüfe, ob das Modell GPU-Beschleunigung verwendet
            gpu_mode = False
            actual_gpu_layers = 0
            
            # Methode 1: Prüfe Modell-Attribute (falls verfügbar)
            if hasattr(self.model, "n_gpu_layers"):
                actual_gpu_layers = getattr(self.model, "n_gpu_layers", 0)
                gpu_mode = actual_gpu_layers > 0
                logger.info(f"Hardware-Modus erkannt über Modell-Attribute: GPU-Layer = {actual_gpu_layers}")
                
            # Methode 2: Prüfe Modell-Eigenschaften über _model (falls verfügbar)
            elif hasattr(self.model, "_model") and hasattr(self.model._model, "n_gpu_layers"):
                actual_gpu_layers = getattr(self.model._model, "n_gpu_layers", 0)
                gpu_mode = actual_gpu_layers > 0
                logger.info(f"Hardware-Modus erkannt über _model-Attribute: GPU-Layer = {actual_gpu_layers}")
                
            # Methode 3: Prüfe, ob CUDA-Umgebungsvariablen gesetzt sind und angeforderte Layer > 0
            elif self.hardware_status.cuda_available and requested_gpu_layers > 0:
                # Wenn CUDA verfügbar ist und GPU-Layer angefordert wurden, gehen wir von GPU-Modus aus
                gpu_mode = True
                actual_gpu_layers = requested_gpu_layers
                logger.info(f"Hardware-Modus basierend auf CUDA-Verfügbarkeit und angeforderten Layern: GPU-Layer = {actual_gpu_layers}")
            
            # Aktualisiere Hardware-Status
            self.hardware_status.mode = HardwareMode.GPU if gpu_mode else HardwareMode.CPU
            self.hardware_status.gpu_layers = actual_gpu_layers
            self.hardware_status.last_checked = time.time()
            
            # Warnungen bei Diskrepanzen
            if requested_gpu_layers > 0 and not gpu_mode:
                logger.warning(f"GPU-Beschleunigung wurde angefordert (Layers: {requested_gpu_layers}), "
                              f"aber das Modell läuft im CPU-Modus.")
            elif requested_gpu_layers == 0 and gpu_mode:
                logger.warning(f"CPU-Modus wurde angefordert, aber das Modell läuft im GPU-Modus "
                              f"mit {actual_gpu_layers} Layern.")
            
            logger.info(f"Hardware-Modus erkannt: {self.hardware_status.mode.value}, GPU-Layer: {self.hardware_status.gpu_layers}")
            
        except Exception as e:
            logger.error(f"Fehler bei der Hardware-Modus-Erkennung: {e}")
            self.hardware_status.mode = HardwareMode.CPU  # Fallback auf CPU im Fehlerfall
            self.hardware_status.gpu_layers = 0

    @handle_errors(return_value="❌ Ein unerwarteter Fehler ist aufgetreten. Bitte versuche es erneut.")
    def chat(self, messages):
        """
        Generiert eine Chat-Antwort vom Modell basierend auf den übergebenen Nachrichten.
        
        Diese Methode sendet eine Anfrage an das geladene Sprachmodell und gibt
        die generierte Antwort zurück. Sie verwendet das Standard-Chat-Format
        des Modells und die konfigurierte Temperatur.
        
        Args:
            messages (list): Liste von Nachrichten im Format [{"role": "...", "content": "..."}]
            
        Returns:
            str: Die generierte Antwort oder eine Fehlermeldung
            
        Raises:
            ModelError: Bei Problemen mit dem Modell oder der Generierung
        """
        if not self.model:
            return "❌ Kein Modell geladen. Bitte lade ein Modell mit !model <n>."
            
        if not isinstance(messages, list) or not messages:
            raise ModelError("Ungültiges Nachrichtenformat")
            
        try:
            # Erstelle einen einfachen Hash der Nachrichten für den Cache
            import hashlib
            message_str = str([msg.get("content", "") for msg in messages])
            query_hash = hashlib.md5(message_str.encode()).hexdigest()
            
            # Prüfe Cache
            if query_hash in self.response_cache:
                logger.info("Verwende gecachte Antwort")
                return self.response_cache[query_hash]
            
            # Zeitmessung starten
            start_time = time.time()
            
            # Validiere Temperatur vor jedem Aufruf
            temp = max(0.0, min(1.0, self.temperature))
            if temp != self.temperature:
                logger.warning(f"Temperatur {self.temperature} außerhalb des gültigen Bereichs, verwende {temp}")
                
            # Verwende die optimierten Inferenz-Parameter
            response = self.model.create_chat_completion(
                messages=messages,
                temperature=temp,
                top_p=self.top_p,
                top_k=self.top_k,
                repeat_penalty=self.repeat_penalty
                # n_threads parameter removed as it's no longer supported
            )
            
            # Zeitmessung beenden
            end_time = time.time()
            inference_time = end_time - start_time
            
            # Performance-Metriken aktualisieren
            self.hardware_status.performance_metrics["last_inference_time"] = inference_time
            self.hardware_status.performance_metrics["avg_inference_time"] = (
                self.hardware_status.performance_metrics.get("avg_inference_time", inference_time) * 0.9 +
                inference_time * 0.1  # Einfacher gleitender Durchschnitt
            )
            
            logger.info(f"Inferenz abgeschlossen in {inference_time:.2f} Sekunden")
            
            # Validiere Antwort
            if not response or "choices" not in response or not response["choices"]:
                raise ModelError("Leere Antwort vom Modell erhalten")
                
            content = response["choices"][0]["message"].get("content", "")
            if not content:
                return "Das Modell hat keine Antwort generiert. Bitte versuche es erneut."
            
            # Cache die Antwort
            if len(self.response_cache) >= self.cache_size:
                # Entferne einen zufälligen Eintrag, wenn der Cache voll ist
                self.response_cache.pop(next(iter(self.response_cache)))
            self.response_cache[query_hash] = content
            
            return content
            
        except KeyError:
            raise ModelError("Unerwartetes Antwortformat vom Modell")
        except Exception as e:
            logger.error(f"Fehler bei der Textgenerierung: {str(e)}", exc_info=SETTINGS.debug)
            raise ModelError(f"Fehler bei der Textgenerierung: {str(e)}")

    def get_hardware_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über den aktuellen Hardware-Status zurück.
        
        Diese Methode stellt Informationen über den aktuellen Hardware-Status
        des Modells bereit, einschließlich des Modus (CPU/GPU) und der Anzahl
        der GPU-Layer, falls im GPU-Modus.
        
        Returns:
            Dict[str, Any]: Ein Dictionary mit Hardware-Informationen
        """
        # Aktualisiere Hardware-Status, falls noch nicht geschehen
        if self.hardware_status.mode == HardwareMode.UNKNOWN and self.model is not None:
            self._detect_hardware_mode()
            
        # Erstelle Hardware-Info-Dictionary
        info = {
            "mode": self.hardware_status.mode.value,
            "gpu_layers": self.hardware_status.gpu_layers,
            "cuda_available": self.hardware_status.cuda_available
        }
        
        # Füge Performance-Metriken hinzu, falls vorhanden
        if self.hardware_status.performance_metrics:
            info["performance_metrics"] = self.hardware_status.performance_metrics
            
        return info
        
    def is_gpu_mode(self) -> bool:
        """
        Prüft, ob das Modell im GPU-Modus läuft.
        
        Returns:
            bool: True, wenn das Modell im GPU-Modus läuft, sonst False
        """
        return self.hardware_status.mode == HardwareMode.GPU
        
    def get_gpu_layers(self) -> int:
        """
        Gibt die Anzahl der verwendeten GPU-Layer zurück.
        
        Returns:
            int: Die Anzahl der GPU-Layer oder 0, wenn im CPU-Modus
        """
        return self.hardware_status.gpu_layers
        
    def serialize_hardware_status(self) -> Dict[str, Any]:
        """
        Serialisiert den Hardware-Status für die Speicherung oder Übertragung.
        
        Returns:
            Dict[str, Any]: Ein serialisierbares Dictionary mit dem Hardware-Status
        """
        status_dict = asdict(self.hardware_status)
        # Konvertiere Enum zu String
        status_dict["mode"] = self.hardware_status.mode.value
        return status_dict
        
    def save_gpu_settings(self, config_path: str = "config/settings.yaml") -> bool:
        """
        Speichert die GPU-Einstellungen in der Konfigurationsdatei.
        
        Diese Methode aktualisiert die GPU-Einstellungen in der Konfigurationsdatei,
        damit sie beim nächsten Start automatisch geladen werden.
        
        Args:
            config_path (str): Pfad zur Konfigurationsdatei
            
        Returns:
            bool: True, wenn die Einstellungen erfolgreich gespeichert wurden, sonst False
        """
        try:
            # Aktuelle Konfiguration laden
            if not os.path.exists(config_path):
                logger.warning(f"Konfigurationsdatei nicht gefunden: {config_path}")
                return False
                
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                
            # Modellkonfiguration aktualisieren oder erstellen
            if "model" not in config:
                config["model"] = {}
                
            # GPU-Einstellungen aktualisieren
            if self.hardware_status.mode == HardwareMode.GPU:
                config["model"]["gpu_layers"] = self.hardware_status.gpu_layers
            else:
                config["model"]["gpu_layers"] = 0
                
            # Konfiguration speichern
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False)
                
            logger.info(f"GPU-Einstellungen gespeichert: gpu_layers={config['model']['gpu_layers']}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der GPU-Einstellungen: {e}")
            return False
            
    def load_gpu_settings(self, config_path: str = "config/settings.yaml") -> Dict[str, Any]:
        """
        Lädt die GPU-Einstellungen aus der Konfigurationsdatei.
        
        Diese Methode liest die GPU-Einstellungen aus der Konfigurationsdatei
        und gibt sie als Dictionary zurück.
        
        Args:
            config_path (str): Pfad zur Konfigurationsdatei
            
        Returns:
            Dict[str, Any]: Die geladenen GPU-Einstellungen oder ein leeres Dictionary
        """
        try:
            # Prüfe, ob die Konfigurationsdatei existiert
            if not os.path.exists(config_path):
                logger.warning(f"Konfigurationsdatei nicht gefunden: {config_path}")
                return {}
                
            # Konfiguration laden
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                
            # GPU-Einstellungen extrahieren
            model_cfg = config.get("model", {})
            gpu_settings = {
                "gpu_layers": model_cfg.get("gpu_layers", 50)
            }
            
            logger.info(f"GPU-Einstellungen geladen: {gpu_settings}")
            return gpu_settings
        except Exception as e:
            logger.error(f"Fehler beim Laden der GPU-Einstellungen: {e}")
            return {}
        
    def chat_stream(self, messages):
        """
        Generiert eine Chat-Antwort als Stream von Tokens.
        
        Diese Methode sendet eine Anfrage an das Sprachmodell und gibt die Antwort
        als Generator zurück, der Token für Token liefert. Dies ermöglicht eine
        flüssigere Benutzererfahrung, da Teile der Antwort angezeigt werden können,
        sobald sie generiert werden.
        
        Args:
            messages (list): Liste von Nachrichten im Format [{"role": "...", "content": "..."}]
            
        Yields:
            str: Einzelne Tokens der generierten Antwort oder eine Fehlermeldung
        """
        if not self.model:
            yield "❌ Kein Modell geladen. Bitte lade ein Modell mit !model <n>."
            return
            
        if not isinstance(messages, list) or not messages:
            logger.error("Ungültiges Nachrichtenformat für Streaming")
            yield "❌ Interner Fehler: Ungültiges Nachrichtenformat."
            return
            
        try:
            # Zeitmessung starten
            start_time = time.time()
            
            # Validiere Temperatur vor jedem Aufruf
            temp = max(0.0, min(1.0, self.temperature))
            if temp != self.temperature:
                logger.warning(f"Temperatur {self.temperature} außerhalb des gültigen Bereichs, verwende {temp}")
                
            # Verwende die optimierten Inferenz-Parameter auch für Streaming
            stream = self.model.create_chat_completion(
                messages=messages,
                temperature=temp,
                top_p=self.top_p,
                top_k=self.top_k,
                repeat_penalty=self.repeat_penalty,
                # n_threads parameter removed as it's no longer supported
                stream=True
            )
            
            token_count = 0
            for chunk in stream:
                if "choices" in chunk:
                    token = chunk["choices"][0]["delta"].get("content", "")
                    if token:
                        token_count += 1
                        yield token
            
            # Zeitmessung beenden
            end_time = time.time()
            streaming_time = end_time - start_time
            
            # Performance-Metriken aktualisieren
            self.hardware_status.performance_metrics["last_streaming_time"] = streaming_time
            self.hardware_status.performance_metrics["tokens_per_second"] = token_count / streaming_time if streaming_time > 0 else 0
            
            logger.info(f"Streaming abgeschlossen in {streaming_time:.2f} Sekunden, {token_count} Tokens generiert")
                        
            # Prüfe, ob überhaupt Tokens generiert wurden
            if token_count == 0:
                logger.warning("Keine Tokens im Stream generiert")
                yield " [Keine Antwort generiert]"
                
        except KeyboardInterrupt:
            # Spezielle Behandlung für Benutzerabbruch
            logger.info("Streaming durch Benutzer abgebrochen")
            yield "\n[Streaming abgebrochen]"
        except Exception as e:
            error_msg = f"❌ Streamingfehler: {str(e)}"
            logger.error(f"Fehler beim Streaming: {str(e)}", exc_info=SETTINGS.debug)
            yield error_msg