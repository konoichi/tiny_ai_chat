# /chatbot/bot.py
"""
Version: 3.0.1
------------------------------
ID: NAVYYARD-REFACTOR-V3-BOT-FIXED-01
Beschreibung: Hauptklasse AbbyBot, die als zentraler Controller fungiert.
FIX: Korrigiert einen ImportError, indem der korrekte Funktionsname
'perform_selftest' aus dem selftest-Modul importiert wird.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
import logging
import os
import yaml
import time
from pathlib import Path
from colorama import Fore, Style, init

# Lokale Importe
from .memory import Memory
from .yaml_persona_manager import YAMLPersonaManager
from .prompter import PromptBuilder
from .model_wrapper import ModelWrapper
# KORRIGIERTER IMPORT HIER:
from .selftest import perform_selftest
from .config import SETTINGS
from .status_banner import StatusBanner
from .tts.manager import TTSManager
from . import bot_model_commands as bmc
from .model_manager import scan_models, load_last_model

init(autoreset=True)

class AbbyBot:
    """
    Hauptklasse des Chatbot-Systems, die alle Komponenten orchestriert.
    Dient als Zustand-Container und Werkzeugkiste für main.py.
    """
    def __init__(self):
        """Initialisiert den Bot und alle seine Sub-Komponenten."""
        self.logger = logging.getLogger("AbbyBot")
        self.memory = Memory()
        self.persona_manager = YAMLPersonaManager(base_path="config", yaml_path="config/personas", default="nova")
        self.prompter = PromptBuilder(self.persona_manager.get_persona())
        self.model = ModelWrapper()
        self.streaming = False
        SETTINGS.debug = False
        
        self.status_banner = StatusBanner(self)
        bmc.bind_abby(self)

        # --- TTS-Manager initialisieren ---
        self.tts_manager = None
        try:
            with open("config/settings.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if "tts" in config:
                self.tts_manager = TTSManager(config["tts"])
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung des TTS-Managers: {e}", exc_info=True)

        # --- Pre-Indexing der Modelle ---
        self.logger.info("Pre-Indexing der Modelle...")
        model_list = scan_models()
        bmc.model_list = model_list
        self.logger.info(f"{len(model_list)} Modelle gefunden und indexiert")

        last = load_last_model(model_list)
        if last:
            ok = self.model.load_model(str(last.path))
            if ok:
                bmc.active_model = last
                print(Fore.YELLOW + f"\n🔁 Letztes Modell automatisch geladen: {last.name}")

    # --- Handler-Methoden (aufgerufen von main.py) ---

    def handle_reset_command(self, user_input):
        self.memory.clear()
        print(Fore.YELLOW + "🧹 Verlauf gelöscht")

    def handle_model_command(self, user_input):
        parts = user_input.strip().split()
        if len(parts) == 2:
            if parts[1] == "last_model":
                print(bmc.handle_model_last())
                return
            if parts[1].isdigit():
                print(bmc.handle_model_select(int(parts[1])))
                return
        elif len(parts) == 1:
            print(bmc.handle_model_info())
            return
        print(Fore.YELLOW + "❓ Ungültige Syntax für !model")

    def handle_models_command(self, user_input):
        verbose = "--verbose" in user_input.lower()
        print(bmc.handle_models_command(verbose))

    def handle_persona_command(self, user_input):
        name = user_input.split("!persona ", 1)[1].strip()
        if not name:
            print(Fore.YELLOW + "⚠️ Bitte gib einen Persona-Namen an.")
            return
        self.persona_manager.load_persona(name)
        self.prompter = PromptBuilder(self.persona_manager.get_persona())
        self.status_banner.update()
        print(Fore.YELLOW + f"🔄 Persona gewechselt zu: {name}")

    def handle_say_command(self, user_input):
        text_to_say = user_input.split("!say ", 1)[1].strip()
        if not text_to_say:
            print(Fore.YELLOW + "Was soll ich sagen? `!say TEXT`")
            return
        if self.tts_manager:
            self.tts_manager.speak(text_to_say)

    def handle_tts_command(self, user_input):
        if not self.tts_manager or not self.tts_manager.is_configured:
            print(Fore.YELLOW + "⚠️ TTS kann nicht verwendet werden (nicht konfiguriert).")
            return
        if "!tts on" in user_input.lower():
            self.tts_manager.enable()
            print(Fore.YELLOW + "🔊 TTS aktiviert.")
        elif "!tts off" in user_input.lower():
            self.tts_manager.disable()
            print(Fore.YELLOW + "🔇 TTS deaktiviert.")
            
    def handle_stream_command(self, user_input):
        if "!stream on" in user_input.lower():
            self.streaming = True
            print(Fore.YELLOW + "🔁 Streaming aktiviert")
        elif "!stream off" in user_input.lower():
            self.streaming = False
            print(Fore.YELLOW + "⏹️ Streaming deaktiviert")

    def handle_debug_command(self, user_input):
        if "!debug on" in user_input.lower():
            SETTINGS.set_debug(True)
            print(Fore.YELLOW + "🐞 Debug-Modus aktiviert")
        elif "!debug off" in user_input.lower():
            SETTINGS.set_debug(False)
            print(Fore.YELLOW + "🚫 Debug-Modus deaktiviert")

    def handle_selftest_command(self, user_input):
        # KORRIGIERTER AUFRUF HIER:
        perform_selftest(self)

    def handle_benchmark_command(self, user_input):
        print(Fore.YELLOW + "Führe Benchmark aus...")
        test_prompt = self.prompter.build([], "Erkläre Quantencomputing in 100 Worten")
        start_time = time.time()
        self.model.chat(test_prompt)
        duration = time.time() - start_time
        print(Fore.YELLOW + f"Benchmark abgeschlossen in {duration:.2f} Sekunden")

    # --- Anzeige-Methoden ---

    def display_status(self, user_input=None):
        self.status_banner.print_status(self)

    def display_hardware_info(self, user_input=None):
        self.status_banner.print_hardware_info(self)

    def display_help(self, user_input=None):
        self.status_banner.print_help()

    def display_banner(self):
        self.status_banner.display()

    # --- Kernlogik ---

    def get_user_input(self):
        """Holt die Benutzereingabe aus der Konsole."""
        return input(Fore.CYAN + "👤 Du: " + Style.RESET_ALL).strip()

    def process_llm_request(self, user_input):
        """Verarbeitet eine normale Benutzereingabe, die an die KI gehen soll."""
        chat_history = self.memory.get_recent()
        prompt = self.prompter.build(chat_history, user_input)

        if self.streaming:
            print(Fore.GREEN + f"🤖 {self.persona_manager.get_current_name().capitalize()}: ", end="", flush=True)
            stream_buffer = ""
            for token in self.model.chat_stream(prompt):
                print(Fore.GREEN + token, end="", flush=True)
                stream_buffer += token
            print()
            answer = stream_buffer.strip()
        else:
            answer = self.model.chat(prompt)
            print(Fore.GREEN + f"🤖 {self.persona_manager.get_current_name().capitalize()}: {answer}")

        self.memory.add_entry(user_input, answer)
        if self.tts_manager and self.tts_manager.enabled:
            self.tts_manager.speak(answer)
