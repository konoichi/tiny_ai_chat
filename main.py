# abby_chatbot/main.py
"""
NavyYard Chatbot - Startpunkt (Version 3.1.0)
-------------------------------------------------
ID: NAVYYARD-GRADIO-MAIN-FIX-01
Beschreibung: Einstiegspunkt für den NavyYard-KI-Chatbot.
ÄNDERUNG: Die Hauptschleife wurde angepasst, um den Rückgabewert von
'process_llm_request' zu verarbeiten. Sie ist jetzt für die Anzeige der
Antwort und die Auslösung von TTS im CLI-Modus verantwortlich.
"""
import os
import logging

os.environ["LLAMA_CUBLAS"] = "1"
from chatbot.bot import AbbyBot

def main():
    """
    Hauptfunktion, die den Chatbot initialisiert und die interaktive Schleife ausführt.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        bot = AbbyBot()

        command_handlers = {
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
            "!exit": lambda _: "exit_signal",
            "!quit": lambda _: "exit_signal",
        }

        bot.display_banner()

        while True:
            user_input = bot.get_user_input()

            if user_input.startswith('!'):
                command_word = user_input.split()[0].lower()
                handler = command_handlers.get(command_word)

                if handler:
                    result = handler(user_input)
                    if result == "exit_signal":
                        print("👋 Abby: Bis bald!")
                        break
                else:
                    print(f"❓ Unbekannter Befehl: '{command_word}'. Tippe '!help' für eine Liste aller Befehle.")

            else:
                # *** DIE ENTSCHEIDENDE ÄNDERUNG ***
                # Wir fangen die Antwort auf...
                response = bot.process_llm_request(user_input)
                # ...geben sie in der Konsole aus...
                bot.display_bot_response(response)
                # ...und kümmern uns um die Sprachausgabe.
                if bot.tts_manager and bot.tts_manager.is_enabled():
                    bot.tts_manager.speak(response)

    except KeyboardInterrupt:
        print("\n👋 Programm durch Benutzer beendet.")
    except Exception as e:
        logging.error(f"Ein kritischer Fehler ist in der Hauptschleife aufgetreten: {e}", exc_info=True)


if __name__ == "__main__":
    main()
