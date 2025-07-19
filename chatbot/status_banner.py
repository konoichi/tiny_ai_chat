# /chatbot/status_banner.py
"""
Version: 3.0.0
------------------------------
ID: NAVYYARD-REFACTOR-V3-STATUSBANNER-01
Beschreibung: Verantwortlich für die Anzeige von Bannern, Statusinformationen und Hilfetexten.

Nach dem Refactoring enthält diese Klasse alle Methoden zur Anzeige von Informationen,
die zuvor teilweise als globale Funktionen in bot.py existierten. Sie ist jetzt
der alleinige Spezialist für alle konsolenbasierten UI-Elemente.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
from colorama import Fore, Style
import os
from . import bot_model_commands as bmc

class StatusBanner:
    def __init__(self, bot):
        """
        Initialisiert den StatusBanner.
        
        Args:
            bot (AbbyBot): Eine Referenz auf die Haupt-Bot-Instanz, um auf
                           Daten wie Modell, Persona etc. zugreifen zu können.
        """
        self.bot = bot

    def display(self):
        """Zeigt den Haupt-Startbanner an."""
        print(Fore.CYAN + "="*50)
        print(Fore.CYAN + "===========Abby Chatbot - Einsatzbereit===========")
        print(Fore.CYAN + "="*50)
        if bmc.active_model:
            print(f"- Aktives Modell : {bmc.active_model.name}")
            if hasattr(self.bot.model, "get_hardware_info"):
                info = self.bot.model.get_hardware_info()
                print(f"- Betriebsmodus : {info.get('mode', 'N/A')} ({info.get('gpu_layers', 0)} Layer)")
        print(f"- Aktive Persona : {self.bot.persona_manager.get_current_name()}")
        print(Fore.CYAN + "="*50)

    def update(self):
        """Aktualisiert den Banner (oder zeigt ihn erneut an)."""
        self.display()

    def print_status(self, bot_instance=None):
        """
        Zeigt den detaillierten Bot-Status an.
        Nimmt optional eine bot_instance an, verwendet aber self.bot.
        """
        bot = self.bot # Nutze die gespeicherte bot-Referenz
        print(Fore.YELLOW + "\n📊 Aktueller Bot-Status:")
        
        if bmc.active_model:
            print(f"- Aktives Modell: {bmc.active_model.name}")
            if hasattr(bot.model, "get_hardware_info"):
                hardware_info = bot.model.get_hardware_info()
                mode = hardware_info.get("mode", "UNKNOWN")
                gpu_layers = hardware_info.get("gpu_layers", 0)
                print(f"- Betriebsmodus: {mode}" + (f" ({gpu_layers} Layer)" if mode == "GPU" else ""))
        
        persona_name = bot.persona_manager.get_current_name()
        print(f"- Aktive Persona: {persona_name}")
        
        if hasattr(bot.persona_manager, "get_yaml_persona"):
            yaml_persona = bot.persona_manager.get_yaml_persona()
            if yaml_persona:
                print(f"  ├ Typ: YAML-Persona")
                if yaml_persona.description:
                    print(f"  ├ Beschreibung: {yaml_persona.description}")
            else:
                print(f"  └ Typ: Text-Persona")
        
        print(f"- Streaming: {'aktiviert' if bot.streaming else 'deaktiviert'}")
        print(f"- Debug-Modus: {'aktiviert' if bot.debug_mode else 'deaktiviert'}")
        print(f"- Verlaufslänge: {len(bot.memory.get_recent())} Einträge")

        if bot.tts_manager:
            tts_status = 'aktiviert' if bot.tts_manager.enabled else 'deaktiviert'
            print(f"- TTS: {tts_status}")

    def print_hardware_info(self, bot_instance=None):
        """Zeigt detaillierte Hardware-Informationen an."""
        bot = self.bot
        print(Fore.YELLOW + "\n💻 Hardware-Informationen:")
        
        if not hasattr(bot, "model") or not hasattr(bot.model, "get_hardware_info"):
            print("❌ Hardware-Informationen nicht verfügbar.")
            return
        
        hardware_info = bot.model.get_hardware_info()
        print(f"- CUDA verfügbar: {'✅' if hardware_info.get('cuda_available') else '❌'}")
        
        print("\nUmgebungsvariablen für GPU-Beschleunigung:")
        print(f"- LLAMA_CUBLAS: {os.environ.get('LLAMA_CUBLAS', 'nicht gesetzt')}")

    def print_help(self):
        """Zeigt das Hilfe-Menü an."""
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
  💀 !selftest               - Systemcheck durchführen
  ⏱️ !benchmark              - Führt einen einfachen Benchmark durch

  Allgemein
  ─────────
  ❓ !help                   - Diese Hilfe anzeigen
  🚪 !exit / !quit           - Abby verlassen
""")
