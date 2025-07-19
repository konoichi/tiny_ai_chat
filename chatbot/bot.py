"""
/chatbot/bot.py
Version: 1.4.5
------------------------------
ID: ABBY-BOT-PY-FINAL-TTS-DELAY-FIX-01
Chat-Bot Abby mit Stream, Debug, Status, Persona-Switching, dynamischem 
Modellmanagement (!model) und optionaler TTS-Integration. Korrigiert das
"Stille"-Problem durch eine konfigurierbare Verzögerung vor der Wiedergabe,
anstelle einer fehlerhaften WAV-Verkettung.

Hauptklasse AbbyBot, die als zentraler Controller für das Chatbot-System fungiert.
Diese Klasse orchestriert die Interaktion zwischen:
- Benutzer-Eingabe und -Ausgabe
- Persona-Management
- Modell-Interaktion und -Verwaltung
- Konversationsgedächtnis
- Kommando-Verarbeitung
- Text-to-Speech (TTS) über einen externen Server

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

import logging
import os
import sys
import traceback
import yaml
import subprocess
import tempfile
import time
import struct
from .memory import Memory, MemoryError
from .persona_manager import PersonaManager, PersonaError
from .yaml_persona_manager import YAMLPersonaManager
from .prompter import PromptBuilder
from .model_wrapper import ModelWrapper
from .selftest import selftest
from .config import SETTINGS
from .error_handler import (
    ChatbotError, ModelError, CommandError, 
    log_error, format_error_for_user, handle_errors
)
from .status_banner import StatusBanner
from .tts.manager import TTSManager # Angepasster Import-Pfad
from colorama import Fore, Style, init

from .bot_model_commands import (
    handle_models_command,
    handle_model_select,
    handle_model_last,
    handle_model_info,
    bind_abby
)
from .model_manager import scan_models, load_last_model


init(autoreset=True)

# suppress llama_perf_context_print unless in debug mode
if "LLAMA_PERF_DISABLE" not in os.environ:
    os.environ["LLAMA_PERF_DISABLE"] = "1"

class AbbyBot:
    """
    Hauptklasse des Chatbot-Systems, die alle Komponenten orchestriert.
    """
    def __init__(self):
        """
        Initialisiert den Chatbot mit allen erforderlichen Komponenten.
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("AbbyBot")
        self.memory = Memory()
        self.persona_manager = YAMLPersonaManager(base_path="config", yaml_path="config/personas", default="Nova")
        self.prompter = PromptBuilder(self.persona_manager.get_persona())
        self.model = ModelWrapper()
        self.streaming = False
        SETTINGS.debug = False
        self._audio_player = "Unbekannt" # Initialwert
        self._player_detected = False # Flag, um die Suche nur einmal auszuführen
        self.tts_pre_play_delay_ms = 250 # Standardwert
        
        self.status_banner = StatusBanner(self)

        bind_abby(self)

        # TTS-Manager initialisieren
        self.tts_manager = None
        try:
            with open("config/settings.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if "tts" in config:
                self.tts_manager = TTSManager(config["tts"])
                self.tts_pre_play_delay_ms = config["tts"].get("pre_play_delay_ms", 250)
                if self.tts_manager.enabled:
                    self.logger.info("TTS-Manager initialisiert. Server-URL: %s", self.tts_manager.server_url)
                else:
                    self.logger.info("TTS ist in der Konfiguration deaktiviert.")
            else:
                self.logger.info("Kein 'tts'-Abschnitt in der Konfiguration gefunden. TTS bleibt deaktiviert.")

        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung des TTS-Managers: {e}", exc_info=True)


        # Pre-Indexing der Modelle
        from . import bot_model_commands as bmc
        from pathlib import Path
        
        self.logger.info("Pre-Indexing der Modelle...")
        model_list = scan_models()
        bmc.model_list = model_list
        self.logger.info(f"{len(model_list)} Modelle gefunden und indexiert")

        default_path = self.model.model_path
        default_model = None
        if default_path:
            default_name = Path(default_path).stem
            default_model = next((m for m in model_list if m.name == default_name), None)
        if default_model:
            bmc.active_model = default_model

        last = load_last_model(model_list)
        if last:
            ok = self.model.load_model(str(last.path))
            if ok:
                bmc.active_model = last
                print(Fore.YELLOW + f"\n🔁 Letztes Modell automatisch geladen: {last.name}")
            else:
                print(Fore.YELLOW + f"\n⚠️ Modell konnte nicht geladen werden: {last.name}")

    def _detect_audio_player(self):
        """Sucht nach einem verfügbaren Audioplayer und speichert das Ergebnis."""
        if self._player_detected:
            return
            
        try:
            subprocess.run(["ffplay", "-version"], check=True, capture_output=True)
            self._audio_player = "ffplay"
            self.logger.info("Audioplayer 'ffplay' gefunden.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                subprocess.run(["aplay", "--version"], check=True, capture_output=True)
                self._audio_player = "aplay"
                self.logger.info("Audioplayer 'aplay' gefunden.")
                if not getattr(self, "_aplay_warning_shown", False):
                    print(Fore.YELLOW + "⚠️ Hinweis: 'ffplay' nicht gefunden. Fallback auf 'aplay'. Für eine bessere Wiedergabe wird die Installation von ffmpeg empfohlen.")
                    self._aplay_warning_shown = True
            except (FileNotFoundError, subprocess.CalledProcessError):
                self.logger.error("Kein Audioplayer (ffplay/aplay) gefunden.")
                self._audio_player = "Keiner"
        
        self._player_detected = True

    def _speak(self, text: str):
        """
        Nutzt den TTSManager, um Text als Audio auszugeben.
        Fügt eine kurze, konfigurierbare Pause vor der Wiedergabe hinzu.
        """
        if not (self.tts_manager and self.tts_manager.enabled and text and self._audio_player not in ["Unbekannt", "Keiner"]):
            return

        audio_data = self.tts_manager.synthesize(text)
        if not audio_data:
            print(Fore.RED + "❌ Audio-Synthese fehlgeschlagen. Läuft der TTS-Server?")
            return

        # Kurze Pause VOR der Wiedergabe, um dem System Zeit zu geben
        time.sleep(self.tts_pre_play_delay_ms / 1000.0)

        if self._audio_player == "ffplay":
            player_command = ["ffplay", "-autoexit", "-nodisp", "-loglevel", "error", "-i", "-"]
        elif self._audio_player == "aplay":
            player_command = ["aplay"]
        else:
            return

        try:
            subprocess.run(
                player_command,
                input=audio_data,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"❌ Fehler beim Abspielen. {self._audio_player} meldet: {e.stderr.decode()}")
        except Exception as e:
            print(Fore.RED + f"❌ Unbekannter Fehler beim Abspielen: {e}")


    def run(self):
        """
        Startet die Hauptschleife des Chatbots.
        """
        try:
            if SETTINGS.debug:
                self.logger.info("AbbyBot gestartet mit Persona '%s'.", self.persona_manager.get_current_name())
            
            self.status_banner.display()
            
            print(Fore.YELLOW + f"🧠 Abby sagt: Frag mich was! (Aktive Persona: {self.persona_manager.get_current_name()})")

            while True:
                try:
                    user_input = input(Fore.CYAN + "👤 Du: " + Style.RESET_ALL)
                    
                    if user_input.lower() in ["exit", "quit"]:
                        print(Fore.GREEN + "👋 Abby: Bis bald!")
                        break

                    if user_input.lower().startswith("!persona "):
                        try:
                            name = user_input.split("!persona ", 1)[1].strip()
                            if not name:
                                print(Fore.YELLOW + "⚠️ Bitte gib einen Persona-Namen an.")
                                continue
                            
                            import time
                            start_time = time.time()
                                
                            self.persona_manager.load_persona(name)
                            self.prompter = PromptBuilder(self.persona_manager.get_persona())
                            
                            if hasattr(self, "status_banner"):
                                try:
                                    self.status_banner.update()
                                except Exception as e:
                                    self.logger.warning(f"Fehler beim Aktualisieren des Status-Banners: {e}")
                            
                            elapsed_time = time.time() - start_time
                            self.logger.info(f"Persona-Wechsel zu {name} in {elapsed_time:.3f} Sekunden abgeschlossen")
                                    
                            print(Fore.YELLOW + f"🔄 Persona gewechselt zu: {name}")
                        except PersonaError as e:
                            print(Fore.RED + format_error_for_user(e))
                            self.logger.error(f"Fehler beim Persona-Wechsel: {e}")
                        continue

                    # TTS-Befehl '!tts on/off'
                    if user_input.lower() in ["!tts on", "!tts off"]:
                        if self.tts_manager and self.tts_manager.is_configured:
                            if user_input.lower() == "!tts on":
                                self.tts_manager.enable()
                                self._detect_audio_player() # Player genau hier suchen!
                                print(Fore.YELLOW + "🔊 TTS aktiviert.")
                            else: # !tts off
                                self.tts_manager.disable()
                                print(Fore.YELLOW + "🔇 TTS deaktiviert.")
                        else:
                            print(Fore.YELLOW + "⚠️ TTS kann nicht verwendet werden, da keine `server_url` in der settings.yaml konfiguriert ist.")
                        continue

                    # TTS-Befehl '!say'
                    if user_input.lower().startswith("!say "):
                        text_to_say = user_input.split("!say ", 1)[1].strip()
                        if not text_to_say:
                            print(Fore.YELLOW + "Was soll ich sagen? `!say TEXT`")
                            continue
                        self._speak(text_to_say)
                        continue

                    if user_input.lower() == "selftest":
                        try:
                            selftest()
                        except Exception as e:
                            print(Fore.RED + f"❌ Selftest fehlgeschlagen: {e}")
                            self.logger.error(f"Selftest-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue

                    if user_input.lower() == "!stream on":
                        self.streaming = True
                        print(Fore.YELLOW + "🔁 Streaming aktiviert")
                        continue

                    if user_input.lower() == "!stream off":
                        self.streaming = False
                        print(Fore.YELLOW + "⏹️ Streaming deaktiviert")
                        continue

                    if user_input.lower() == "!debug on":
                        SETTINGS.set_debug(True)
                        os.environ["LLAMA_PERF_DISABLE"] = "0"
                        print(Fore.YELLOW + "🐞 Debug-Modus aktiviert")
                        continue

                    if user_input.lower() == "!debug off":
                        SETTINGS.set_debug(False)
                        os.environ["LLAMA_PERF_DISABLE"] = "1"
                        print(Fore.YELLOW + "🚫 Debug-Modus deaktiviert")
                        continue

                    if user_input.lower() == "!status":
                        try:
                            print_status(self)
                        except Exception as e:
                            print(Fore.RED + f"❌ Fehler beim Anzeigen des Status: {e}")
                            self.logger.error(f"Status-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue

                    if user_input.lower() == "!reset":
                        try:
                            self.memory.clear()
                            print(Fore.YELLOW + "🧹 Verlauf gelöscht")
                        except Exception as e:
                            print(Fore.RED + f"❌ Fehler beim Löschen des Verlaufs: {e}")
                            self.logger.error(f"Reset-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue

                    if user_input.lower() == "!help":
                        print_help()
                        continue
                        
                    if user_input.lower() == "!hardware":
                        try:
                            print_hardware_info(self)
                        except Exception as e:
                            print(Fore.RED + f"❌ Fehler beim Anzeigen der Hardware-Informationen: {e}")
                            self.logger.error(f"Hardware-Info-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue
                        
                    if user_input.lower() == "!benchmark":
                        try:
                            print(Fore.YELLOW + "Führe Benchmark aus...")
                            import time
                            test_prompt = self.prompter.build([], "Erkläre Quantencomputing in 100 Worten")
                            start_time = time.time()
                            self.model.chat(test_prompt)
                            end_time = time.time()
                            duration = end_time - start_time
                            print(Fore.YELLOW + f"Benchmark abgeschlossen in {duration:.2f} Sekunden")
                            if hasattr(self.model, "hardware_status") and hasattr(self.model.hardware_status, "performance_metrics"):
                                metrics = self.model.hardware_status.performance_metrics
                                if metrics:
                                    print(Fore.YELLOW + "Performance-Metriken:")
                                    for key, value in metrics.items():
                                        if isinstance(value, float):
                                            print(f"- {key}: {value:.2f}")
                                        else:
                                            print(f"- {key}: {value}")
                        except Exception as e:
                            print(Fore.RED + f"❌ Benchmark fehlgeschlagen: {e}")
                            self.logger.error(f"Benchmark-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue

                    if user_input.lower().startswith("!models"):
                        try:
                            verbose = "--verbose" in user_input.lower()
                            print(handle_models_command(verbose))
                        except Exception as e:
                            print(Fore.RED + f"❌ Fehler beim Auflisten der Modelle: {e}")
                            self.logger.error(f"Models-Befehl-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue

                    if user_input.lower().startswith("!model"):
                        try:
                            parts = user_input.strip().split()
                            if len(parts) == 2:
                                if parts[1] == "last_model":
                                    print(handle_model_last())
                                    continue
                                if parts[1].isdigit():
                                    print(handle_model_select(int(parts[1])))
                                    continue
                            elif len(parts) == 1:
                                print(handle_model_info())
                                continue
                            print(Fore.YELLOW + "❓ Ungültige Syntax für !model")
                        except Exception as e:
                            print(Fore.RED + f"❌ Fehler bei Modell-Befehl: {e}")
                            self.logger.error(f"Model-Befehl-Fehler: {e}", exc_info=SETTINGS.debug)
                        continue
                        
                    # Normale Konversation
                    try:
                        chat_history = self.memory.get_recent()
                        prompt = self.prompter.build(chat_history, user_input)

                        if SETTINGS.debug:
                            self.logger.info("Prompt: %s", prompt)

                        if self.streaming:
                            print(Fore.GREEN + f"🤖 {self.persona_manager.get_current_name().capitalize()}: ", end="", flush=True)
                            stream_buffer = ""
                            try:
                                for token in self.model.chat_stream(prompt):
                                    print(Fore.GREEN + token, end="", flush=True)
                                    stream_buffer += token
                                print()
                                answer = stream_buffer.strip() or "[Streaming: keine Ausgabe]"
                            except KeyboardInterrupt:
                                print(Fore.YELLOW + "\n[Streaming abgebrochen]")
                                answer = stream_buffer.strip() + " [abgebrochen]"
                        else:
                            answer = self.model.chat(prompt)
                            print(Fore.GREEN + f"🤖 {self.persona_manager.get_current_name().capitalize()}: {answer}")

                        self.memory.add_entry(user_input, answer)
                        self._speak(answer) # HIER WIRD DIE ANTWORT GESPROCHEN
                        
                    except MemoryError as e:
                        print(Fore.RED + format_error_for_user(e))
                        self.logger.error(f"Gedächtnis-Fehler: {e}", exc_info=SETTINGS.debug)
                    except ModelError as e:
                        print(Fore.RED + format_error_for_user(e))
                        self.logger.error(f"Modell-Fehler: {e}", exc_info=SETTINGS.debug)
                    except Exception as e:
                        print(Fore.RED + f"❌ Unerwarteter Fehler: {e}")
                        self.logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
                        
                except KeyboardInterrupt:
                    print(Fore.YELLOW + "\n⚠️ Eingabe abgebrochen. Drücke Ctrl+C erneut zum Beenden oder gib 'exit' ein.")
                except EOFError:
                    print(Fore.YELLOW + "\n⚠️ EOF erkannt. Beende Programm...")
                    break
                except Exception as e:
                    print(Fore.RED + f"❌ Kritischer Fehler bei der Eingabeverarbeitung: {e}")
                    self.logger.critical(f"Eingabeverarbeitungsfehler: {e}", exc_info=True)
                    
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n👋 Programm durch Benutzer beendet.")
        except Exception as e:
            print(Fore.RED + f"❌ Kritischer Fehler: {e}")
            self.logger.critical(f"Kritischer Fehler in der Hauptschleife: {e}", exc_info=True)
            raise


def print_status(bot):
    print(Fore.YELLOW + "\n📊 Aktueller Bot-Status:")
    
    from . import bot_model_commands as bmc
    if bmc.active_model:
        print(f"- Aktives Modell: {bmc.active_model.name}")
        
        if hasattr(bot.model, "get_hardware_info"):
            hardware_info = bot.model.get_hardware_info()
            mode = hardware_info.get("mode", "UNKNOWN")
            gpu_layers = hardware_info.get("gpu_layers", 0)
            
            if mode == "GPU":
                print(f"- Betriebsmodus: GPU ({gpu_layers} Layer)")
            else:
                print(f"- Betriebsmodus: {mode}")
    
    persona_name = bot.persona_manager.get_current_name()
    print(f"- Aktive Persona: {persona_name}")
    
    if hasattr(bot.persona_manager, "get_yaml_persona"):
        yaml_persona = bot.persona_manager.get_yaml_persona()
        if yaml_persona:
            print(f"  ├ Typ: YAML-Persona")
            if yaml_persona.description:
                print(f"  ├ Beschreibung: {yaml_persona.description}")
            if yaml_persona.personality.get('tone'):
                print(f"  ├ Tonfall: {yaml_persona.personality.get('tone')}")
            if yaml_persona.style.get('language'):
                print(f"  └ Sprache: {yaml_persona.style.get('language')}")
        else:
            print(f"  └ Typ: Text-Persona")
    
    print(f"- Streaming: {'aktiviert' if bot.streaming else 'deaktiviert'}")
    print(f"- Debug-Modus: {'aktiviert' if SETTINGS.debug else 'deaktiviert'}")
    print(f"- Verlaufslänge: {len(bot.memory.get_recent())} Einträge")

    # TTS Status
    if bot.tts_manager:
        tts_status = 'aktiviert' if bot.tts_manager.enabled else 'deaktiviert'
        print(f"- TTS: {tts_status}")
        if bot.tts_manager.is_configured:
            print(f"  ├ Server: {bot.tts_manager.server_url}")
            player = getattr(bot, "_audio_player", "Unbekannt")
            print(f"  └ Player: {player}")


def print_hardware_info(bot):
    print(Fore.YELLOW + "\n💻 Hardware-Informationen:")
    
    if not hasattr(bot, "model") or not hasattr(bot.model, "get_hardware_info"):
        print("❌ Hardware-Informationen nicht verfügbar.")
        return
    
    hardware_info = bot.model.get_hardware_info()
    
    mode = hardware_info.get("mode", "UNKNOWN")
    gpu_layers = hardware_info.get("gpu_layers", 0)
    cuda_available = hardware_info.get("cuda_available", False)
    
    import platform
    system_info = platform.uname()
    
    print(f"- Betriebssystem: {system_info.system} {system_info.release}")
    print(f"- Prozessor: {system_info.processor}")
    print(f"- Hardware-Modus: {mode}")
    
    if mode == "GPU":
        print(f"- GPU-Layer: {gpu_layers}")
    
    print(f"- CUDA verfügbar: {'✅' if cuda_available else '❌'}")
    
    print("\nUmgebungsvariablen für GPU-Beschleunigung:")
    print(f"- LLAMA_CUBLAS: {os.environ.get('LLAMA_CUBLAS', 'nicht gesetzt')}")
    print(f"- CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'nicht gesetzt')}")
    
    performance_metrics = hardware_info.get("performance_metrics", {})
    if performance_metrics:
        print("\nPerformance-Metriken:")
        for key, value in metrics.items():
            print(f"- {key}: {value}")
    
    from . import bot_model_commands as bmc
    if bmc.active_model:
        print(f"\nAktives Modell: {bmc.active_model.name}")
        
        if hasattr(bmc.active_model, "quantization") and bmc.active_model.quantization:
            from .utils.ram_estimator import format_ram_info
            try:
                ram_info = format_ram_info(bmc.active_model.quantization, bmc.active_model.context_length or 4096)
                print(f"- Geschätzter RAM-Bedarf: {ram_info}")
            except Exception as e:
                print(f"- RAM-Schätzung nicht verfügbar: {e}")


def print_help():
    print(Fore.YELLOW + """
🆘 Verfügbare Befehle:

  Modell & Persona
  ────────────────
  📦 !models [--verbose]     - Verfügbare Modelle auflisten
  🔁 !model <n>              - Modell mit Index laden
  📁 !model last_model       - Letztes Modell erneut laden
  ℹ️  !model                 - Infos zum aktiven Modell (inkl. RAM)
  👤 !persona <name>         - Aktive Persona wechseln

  Interaktion & Ausgabe
  ─────────────────────
  🔊 !say <text>             - Text mit TTS sprechen lassen
  🔊 !tts on/off             - TTS zur Laufzeit an-/ausschalten
  🔁 !stream on/off          - Streaming-Modus aktivieren/deaktivieren

  System & Debugging
  ──────────────────
  📊 !status                 - Status anzeigen
  💻 !hardware               - Detaillierte Hardware-Informationen anzeigen
  🐞 !debug on/off           - Debug-Modus aktivieren/deaktivieren
  🧹 !reset                  - Chatverlauf löschen
  💀 selftest                - Systemcheck durchführen

  Allgemein
  ─────────
  ❓ !help                   - Diese Hilfe anzeigen
  🚪 exit / quit             - Abby verlassen
""")
