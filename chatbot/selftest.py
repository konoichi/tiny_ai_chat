# /chatbot/selftest.py
"""
Version: 3.0.2
------------------------------
ID: NAVYYARD-REFACTOR-V3-SELFTEST-CHAT-FIX-01
Beschreibung: Führt einen System-Selbsttest durch.
FIX: Der PromptBuilder-Test wurde angepasst, um das neue Chat-Format
(Liste von Dictionaries) korrekt zu validieren, anstatt nach einem
einfachen String zu suchen.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
import logging
from colorama import Fore

def perform_selftest(bot):
    """
    Führt einen umfassenden Selbsttest auf der übergebenen bot-Instanz durch.
    
    Args:
        bot (AbbyBot): Die aktive Instanz des Bots, deren Komponenten
                       getestet werden sollen.
    """
    print("--- NavyYard Selftest ---")
    tests_passed = True  # Wir verfolgen den Erfolg mit
    
    # --- Test 1: Memory-Modul ---
    print("🧠 Teste Memory-Modul...")
    try:
        bot.memory.add_entry("test_user", "test_assistant")
        if len(bot.memory.get_recent()) > 0:
            print(Fore.GREEN + "  ✅ Memory-Modul funktioniert korrekt")
            bot.memory.clear() # Aufräumen
        else:
            raise Exception("Eintrag wurde nicht hinzugefügt.")
    except Exception as e:
        print(Fore.RED + f"  ❌ FEHLER im Memory-Modul: {e}")
        tests_passed = False

    # --- Test 2: PromptBuilder-Modul (ANGEPASST AN CHAT-FORMAT) ---
    print("📝 Teste PromptBuilder-Modul...")
    try:
        test_input = "Test-Eingabe"
        # Der Prompt ist jetzt eine Liste von Dictionaries
        prompt_list = bot.prompter.build([], test_input)
        
        # Wir suchen die Nachricht mit der Rolle 'user'
        user_message_found = False
        if isinstance(prompt_list, list):
            for message in prompt_list:
                if isinstance(message, dict) and message.get('role') == 'user' and message.get('content') == test_input:
                    user_message_found = True
                    break
        
        if user_message_found:
            print(Fore.GREEN + "  ✅ PromptBuilder-Modul funktioniert korrekt (Chat-Format validiert)")
        else:
            # Wenn der Test fehlschlägt, zeigen wir genau, was los ist.
            print(Fore.RED + f"  ❌ FEHLER im PromptBuilder-Modul: Die 'user'-Nachricht wurde nicht korrekt im Prompt gefunden.")
            print(Fore.YELLOW + f"  - Erwartet: Eine Nachricht mit 'role': 'user' und 'content': '{test_input}'")
            print(Fore.YELLOW + f"  - Erhalten (Prompt-Struktur): {prompt_list}")
            tests_passed = False
    except Exception as e:
        print(Fore.RED + f"  ❌ FEHLER im PromptBuilder-Modul: {e}")
        tests_passed = False

    # --- Test 3: Persona-System ---
    print("👤 Teste YAML-Persona-System...")
    try:
        persona_name_to_test = 'nova' 
        if bot.persona_manager.load_persona(persona_name_to_test):
             print(Fore.GREEN + f"  ✅ YAML-Persona '{persona_name_to_test}' erfolgreich geladen.")
        else:
            raise Exception(f"Konnte Persona '{persona_name_to_test}' nicht laden.")
    except Exception as e:
        logging.error(f"Fehler im Persona-System-Test: {e}", exc_info=True)
        print(Fore.RED + f"  ❌ FEHLER beim Laden der YAML-Persona: {e}")
        tests_passed = False

    # --- Test 4: Modellverfügbarkeit ---
    print("🧠 Teste Modellverfügbarkeit...")
    from . import bot_model_commands as bmc
    if bmc.model_list and len(bmc.model_list) > 0:
        print(Fore.GREEN + f"  ✅ {len(bmc.model_list)} GGUF-Modelle gefunden")
    else:
        print(Fore.YELLOW + "  ⚠️ Keine GGUF-Modelle gefunden")

    # --- Zusammenfassung ---
    print("\n--- Selftest-Zusammenfassung ---")
    if tests_passed:
        print(Fore.GREEN + "✅ Alle kritischen Tests erfolgreich bestanden. NavyYard ist bereit.")
    else:
        print(Fore.RED + "❌ Mindestens ein Test ist fehlgeschlagen. Bitte überprüfe die Logs.")
