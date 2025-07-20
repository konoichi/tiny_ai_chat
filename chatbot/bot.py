# /chatbot/bot.py
"""
Version: 4.1.0
------------------------------
ID: NAVYYARD-GRADIO-BOT-STREAMING-FIX-01
Beschreibung: Hauptklasse AbbyBot, die als zentraler Controller fungiert.
FEATURE: Fügt die neue Methode 'process_llm_request_stream' hinzu.
Diese Methode ist ein Generator, der die Antwort der KI Wort für Wort
'yielded', um Live-Streaming in der Gradio-GUI zu ermöglichen.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
# (Imports und __init__ bleiben gleich wie in der vorherigen Version)
import logging
import os
import yaml
import time
from pathlib import Path
from colorama import Fore, Style, init

from .memory import Memory
from .yaml_persona_manager import YAMLPersonaManager
from .prompter import PromptBuilder
from .model_wrapper import ModelWrapper
from .selftest import perform_selftest
from .config import SETTINGS
from .status_banner import StatusBanner
from .tts.manager import TTSManager
from . import bot_model_commands as bmc
from .model_manager import scan_models, load_last_model

init(autoreset=True)

class AbbyBot:
    def __init__(self):
        # ... (der __init__-Block bleibt unverändert)
        self.logger = logging.getLogger("AbbyBot")
        self.memory = Memory()
        self.persona_manager = YAMLPersonaManager(base_path="config", yaml_path="config/personas", default="nova")
        self.prompter = PromptBuilder(self.persona_manager.get_persona())
        self.model = ModelWrapper()
        self.streaming = False
        SETTINGS.debug = False
        self.status_banner = StatusBanner(self)
        bmc.bind_abby(self)
        self.tts_manager = None
        try:
            with open("config/settings.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if "tts" in config:
                self.tts_manager = TTSManager(config["tts"])
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung des TTS-Managers: {e}", exc_info=True)
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

    # --- Handler-Methoden (bleiben unverändert) ---
    def handle_reset_command(self, user_input):
        self.memory.clear()
        print(Fore.YELLOW + "🧹 Verlauf gelöscht")

    def handle_model_command(self, user_input):
        parts = user_input.strip().split()
        if len(parts) >= 2:
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
        parts = user_input.split("!say ", 1)
        if len(parts) > 1 and parts[1].strip():
            text_to_say = parts[1].strip()
            if self.tts_manager:
                self.tts_manager.speak(text_to_say)
        else:
            print(Fore.YELLOW + "Was soll ich sagen? `!say TEXT`")

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
        perform_selftest(self)

    def handle_benchmark_command(self, user_input):
        print(Fore.YELLOW + "Führe Benchmark aus...")
        test_prompt = self.prompter.build([], "Erkläre Quantencomputing in 100 Worten")
        start_time = time.time()
        self.model.chat(test_prompt)
        duration = time.time() - start_time
        print(Fore.YELLOW + f"Benchmark abgeschlossen in {duration:.2f} Sekunden")

    def display_status(self, user_input=None):
        self.status_banner.print_status(self)

    def display_hardware_info(self, user_input=None):
        self.status_banner.print_hardware_info(self)

    def display_help(self, user_input=None):
        self.status_banner.print_help()

    def display_banner(self):
        self.status_banner.display()

    def get_user_input(self):
        return input(Fore.CYAN + "👤 Du: " + Style.RESET_ALL).strip()
        
    def display_bot_response(self, text):
        print(Fore.GREEN + f"🤖 {self.persona_manager.get_current_name().capitalize()}: {text}")

    # --- Kernlogik ---

    def process_llm_request(self, user_input: str) -> str:
        """
        Verarbeitet eine normale Benutzereingabe und GIBT die volle Antwort ZURÜCK.
        Wird von der CLI (main.py) verwendet.
        """
        chat_history = self.memory.get_recent()
        prompt = self.prompter.build(chat_history, user_input)
        answer = self.model.chat(prompt)
        self.memory.add_entry(user_input, answer)
        return answer

    def process_llm_request_stream(self, user_input: str):
        """
        NEUE METHODE: Verarbeitet eine Benutzereingabe und YIELDED die Antwort
        Stück für Stück. Wird von der Gradio-GUI verwendet.
        """
        chat_history = self.memory.get_recent()
        prompt = self.prompter.build(chat_history, user_input)
        
        full_response = ""
        # Wir iterieren durch den Stream vom ModelWrapper
        for token in self.model.chat_stream(prompt):
            full_response += token
            # Wir geben nach jedem Token den bisherigen Gesamttext zurück
            yield full_response
        
        # Nachdem der Stream beendet ist, speichern wir die volle Antwort im Gedächtnis.
        self.memory.add_entry(user_input, full_response)
