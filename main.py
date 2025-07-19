# abby_chatbot/main.py
"""
NavyYard Chatbot - Startpunkt (Version 3.0.0)
-------------------------------------------------
ID: NAVYYARD-REFACTOR-V3-MAIN-01
Autor: Stephan Wilkens / Abby-System
Beschreibung: Neuer Haupteinstiegspunkt für den NavyYard-Chatbot.

Dieses Modul implementiert die neue, saubere Architektur. Es enthält die
Haupt-Eingabeschleife und einen "Command Dispatcher" (Schalttafel), der
Benutzereingaben analysiert und an die entsprechenden Handler-Methoden
in der AbbyBot-Klasse weiterleitet. Die Logik ist hier, der Zustand im Bot.
"""
import os
import logging

# WICHTIG: Setze die Umgebungsvariable, BEVOR irgendetwas von llama_cpp importiert wird.
# Dies aktiviert die GPU-Beschleunigung, falls eine kompatible GPU vorhanden ist.
os.environ["LLAMA_CUBLAS"] = "1"

# Importiere die Haupt-Bot-Klasse erst nach dem Setzen der Umgebungsvariable.
from chatbot.bot import AbbyBot

def main():
    """
    Hauptfunktion, die den Chatbot initialisiert und die interaktive Schleife ausführt.
    """
    # --- Initialisierung ---
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # Erstelle eine Instanz unseres Bots. Sie enthält alle Manager und Zustände.
        bot = AbbyBot()

        # --- Befehls-Schalttafel (Command Dispatcher) ---
        # Dies ist eine saubere Methode, um Benutzereingaben auf die richtigen
        # Funktionen im Bot abzubilden. Jeder Befehl hat einen direkten Draht.
        command_handlers = {
            # Der Key ist der Befehl, der Value ist die Funktion, die aufgerufen wird.
            "!help": bot.display_help,
            "!reset": bot.handle_reset_command,
            "!model": bot.handle_model_command,
            "!models": bot.handle_models_command,
            "!persona": bot.handle_persona_command,
            "!say": bot.handle_say_command,
            "!tts": bot.handle_tts_command,
            "!status": bot.display_status,
            "!hardware": bot.display_hardware_info,
            "!debug": bot.handle_debug_command,
            "!stream": bot.handle_stream_command,
            "!selftest": bot.handle_selftest_command,
            "!benchmark": bot.handle_benchmark_command,
            # Befehle zum Beenden der Schleife
            "!exit": lambda _: "exit_signal",
            "!quit": lambda _: "exit_signal",
        }

        # Zeige den Start-Banner an, wenn alles bereit ist.
        bot.display_banner()

        # --- Haupt-Eingabeschleife ---
        while True:
            user_input = bot.get_user_input()

            # Prüfe, ob die Eingabe ein Systembefehl ist.
            if user_input.startswith('!'):
                command_word = user_input.split()[0].lower()
                # Suche den passenden Handler in unserer Schalttafel.
                handler = command_handlers.get(command_word)

                if handler:
                    # Wenn ein Handler gefunden wurde, führe ihn aus.
                    result = handler(user_input)
                    if result == "exit_signal":
                        print("👋 Abby: Bis bald!")
                        break
                else:
                    # Wenn der Befehl unbekannt ist, gib eine klare Rückmeldung.
                    print(f"❓ Unbekannter Befehl: '{command_word}'. Tippe '!help' für eine Liste aller Befehle.")

            # Wenn es kein Befehl ist, wird die Eingabe an das LLM weitergeleitet.
            else:
                bot.process_llm_request(user_input)

    except KeyboardInterrupt:
        # Fängt Strg+C ab, um einen sauberen Abbruch zu ermöglichen.
        print("\n👋 Programm durch Benutzer beendet.")
    except Exception as e:
        # Fängt alle anderen unerwarteten Fehler ab und loggt sie.
        logging.error(f"Ein kritischer Fehler ist in der Hauptschleife aufgetreten: {e}", exc_info=True)


if __name__ == "__main__":
    # Dieser Block wird nur ausgeführt, wenn das Skript direkt gestartet wird.
    main()
