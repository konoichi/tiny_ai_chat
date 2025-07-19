# abby_chatbot/chatbot/selftest.py
"""
Selftest-Modul für Abby Chatbot
Prüft Basisfunktionen & Module

Dieses Modul implementiert eine einfache Selbsttest-Funktion, die grundlegende
Komponenten des Chatbot-Systems überprüft. Es wird verwendet, um sicherzustellen,
dass die Kernfunktionalitäten korrekt arbeiten, ohne dass ein vollständiger
Testlauf des gesamten Systems erforderlich ist.

Der Selftest überprüft:
- Die Funktionalität des Memory-Moduls
- Die Funktionalität des PromptBuilder-Moduls
- Die korrekte Interaktion zwischen diesen Komponenten
- Die Verfügbarkeit und Lesbarkeit von Konfigurationsdateien
- Die Verfügbarkeit von Modellen

Diese Tests sind bewusst einfach gehalten und dienen hauptsächlich als schnelle
Diagnose für Benutzer, die Probleme mit dem System haben könnten.
"""
import os
import logging
import traceback
from colorama import Fore

# Logger für dieses Modul
logger = logging.getLogger("Selftest")
def selftest():
    """
    Führt einen umfassenden Selbsttest der Kernkomponenten des Chatbot-Systems durch.
    
    Diese Funktion überprüft die grundlegenden Funktionalitäten des Systems:
    1. Initialisierung und Verwendung des Memory-Moduls
    2. Initialisierung und Verwendung des PromptBuilder-Moduls
    3. Korrekte Formatierung der erzeugten Prompts
    4. Verfügbarkeit und Lesbarkeit von Konfigurationsdateien
    5. Verfügbarkeit von Modellverzeichnissen
    
    Die Funktion gibt detaillierte Statusmeldungen auf der Konsole aus und
    protokolliert Fehler für die spätere Diagnose.
    
    Returns:
        None: Die Funktion gibt keinen Wert zurück, sondern druckt Statusmeldungen
    """
    print(Fore.YELLOW + "--- NavyYard Selftest ---")
    
    # Sammle Testergebnisse
    results = {
        "memory": {"status": "nicht getestet", "details": ""},
        "prompter": {"status": "nicht getestet", "details": ""},
        "config": {"status": "nicht getestet", "details": ""},
        "models": {"status": "nicht getestet", "details": ""},
        "yaml_personas": {"status": "nicht getestet", "details": ""}
    }
    
    try:
        # Test 1: Memory-Modul
        print(Fore.CYAN + "🧠 Teste Memory-Modul...")
        try:
            from .memory import Memory
            mem = Memory()
            mem.add_entry("Hallo?", "Na endlich!")
            assert len(mem.get_recent()) == 1, "Memory sollte einen Eintrag enthalten"
            mem.clear()
            assert len(mem.get_recent()) == 0, "Memory sollte leer sein nach clear()"
            results["memory"] = {"status": "ok", "details": "Alle Tests bestanden"}
            print(Fore.GREEN + "  ✅ Memory-Modul funktioniert korrekt")
        except ImportError as e:
            results["memory"] = {"status": "fehler", "details": f"Import-Fehler: {e}"}
            print(Fore.RED + f"  ❌ Memory-Modul konnte nicht importiert werden: {e}")
            logger.error(f"Memory-Modul Import-Fehler: {e}")
        except Exception as e:
            results["memory"] = {"status": "fehler", "details": str(e)}
            print(Fore.RED + f"  ❌ Memory-Test fehlgeschlagen: {e}")
            logger.error(f"Memory-Test fehlgeschlagen: {e}", exc_info=True)

        # Test 2: PromptBuilder-Modul
        print(Fore.CYAN + "📝 Teste PromptBuilder-Modul...")
        try:
            from .prompter import PromptBuilder
            pb = PromptBuilder("Test-Persona")
            # Teste mit leerem Verlauf
            prompt_empty = pb.build([], "Test-Eingabe")
            assert isinstance(prompt_empty, list), "Prompt sollte eine Liste sein"
            assert len(prompt_empty) >= 2, "Prompt sollte mindestens System- und User-Nachricht enthalten"
            assert prompt_empty[0]["role"] == "system", "Erste Nachricht sollte System-Rolle haben"
            assert prompt_empty[-1]["content"] == "Test-Eingabe", "Letzte Nachricht sollte die Benutzereingabe sein"
            
            # Teste mit Verlauf
            test_history = [("Frage 1", "Antwort 1"), ("Frage 2", "Antwort 2")]
            prompt_history = pb.build(test_history, "Frage 3")
            assert len(prompt_history) == 6, "Prompt sollte 6 Nachrichten enthalten (1 System + 4 Verlauf + 1 Aktuell)"
            
            results["prompter"] = {"status": "ok", "details": "Alle Tests bestanden"}
            print(Fore.GREEN + "  ✅ PromptBuilder-Modul funktioniert korrekt")
        except ImportError as e:
            results["prompter"] = {"status": "fehler", "details": f"Import-Fehler: {e}"}
            print(Fore.RED + f"  ❌ PromptBuilder-Modul konnte nicht importiert werden: {e}")
            logger.error(f"PromptBuilder-Modul Import-Fehler: {e}")
        except Exception as e:
            results["prompter"] = {"status": "fehler", "details": str(e)}
            print(Fore.RED + f"  ❌ PromptBuilder-Test fehlgeschlagen: {e}")
            logger.error(f"PromptBuilder-Test fehlgeschlagen: {e}", exc_info=True)

        # Test 3: Konfigurationsdateien
        print(Fore.CYAN + "⚙️ Teste Konfigurationsdateien...")
        try:
            config_path = "config/settings.yaml"
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")
                
            # Teste Persona-Dateien
            persona_files = [f for f in os.listdir("config") if f.endswith(".txt")]
            if not persona_files:
                print(Fore.YELLOW + "  ⚠️ Keine Persona-Dateien gefunden")
            else:
                print(Fore.GREEN + f"  ✅ {len(persona_files)} Persona-Dateien gefunden")
                
            results["config"] = {"status": "ok", "details": f"{len(persona_files)} Persona-Dateien gefunden"}
            print(Fore.GREEN + "  ✅ Konfigurationsdateien sind verfügbar")
        except Exception as e:
            results["config"] = {"status": "fehler", "details": str(e)}
            print(Fore.RED + f"  ❌ Konfigurationstest fehlgeschlagen: {e}")
            logger.error(f"Konfigurationstest fehlgeschlagen: {e}", exc_info=True)

        # Test 4: Modellverzeichnis
        print(Fore.CYAN + "🧠 Teste Modellverfügbarkeit...")
        try:
            models_dir = "models"
            if not os.path.exists(models_dir) or not os.path.isdir(models_dir):
                print(Fore.YELLOW + f"  ⚠️ Modellverzeichnis nicht gefunden: {models_dir}")
                results["models"] = {"status": "warnung", "details": "Modellverzeichnis nicht gefunden"}
            else:
                model_files = [f for f in os.listdir(models_dir) if f.endswith(".gguf")]
                if not model_files:
                    print(Fore.YELLOW + "  ⚠️ Keine GGUF-Modelle im Modellverzeichnis gefunden")
                    results["models"] = {"status": "warnung", "details": "Keine GGUF-Modelle gefunden"}
                else:
                    print(Fore.GREEN + f"  ✅ {len(model_files)} GGUF-Modelle gefunden")
                    results["models"] = {"status": "ok", "details": f"{len(model_files)} Modelle verfügbar"}
        except Exception as e:
            results["models"] = {"status": "fehler", "details": str(e)}
            print(Fore.RED + f"  ❌ Modelltest fehlgeschlagen: {e}")
            logger.error(f"Modelltest fehlgeschlagen: {e}", exc_info=True)
            
        # Test 5: YAML-Persona-System
        print(Fore.CYAN + "👤 Teste YAML-Persona-System...")
        try:
            from .yaml_persona_manager import YAMLPersonaManager, YAMLPersona
            
            # Teste YAMLPersonaManager-Initialisierung
            yaml_manager = YAMLPersonaManager()
            
            # Prüfe, ob das YAML-Personas-Verzeichnis existiert
            yaml_personas_dir = "config/personas"
            if not os.path.exists(yaml_personas_dir):
                print(Fore.YELLOW + f"  ⚠️ YAML-Personas-Verzeichnis nicht gefunden, wird erstellt: {yaml_personas_dir}")
                os.makedirs(yaml_personas_dir, exist_ok=True)
            
            # Prüfe, ob YAML-Persona-Dateien existieren
            yaml_files = [f for f in os.listdir(yaml_personas_dir) if f.endswith(".yaml")]
            if not yaml_files:
                print(Fore.YELLOW + "  ⚠️ Keine YAML-Persona-Dateien gefunden")
                results["yaml_personas"] = {"status": "warnung", "details": "Keine YAML-Persona-Dateien gefunden"}
            else:
                print(Fore.GREEN + f"  ✅ {len(yaml_files)} YAML-Persona-Dateien gefunden")
                
                # Teste das Laden einer YAML-Persona
                test_persona_name = yaml_files[0][:-5]  # Entferne .yaml
                yaml_persona = yaml_manager.load_yaml_persona(test_persona_name)
                
                if yaml_persona:
                    print(Fore.GREEN + f"  ✅ YAML-Persona '{test_persona_name}' erfolgreich geladen")
                    
                    # Teste die Prompt-Generierung
                    full_prompt = yaml_persona.get_full_prompt()
                    assert full_prompt, "YAML-Persona sollte einen vollständigen Prompt generieren können"
                    
                    results["yaml_personas"] = {"status": "ok", "details": f"{len(yaml_files)} YAML-Personas verfügbar"}
                else:
                    print(Fore.YELLOW + f"  ⚠️ Konnte YAML-Persona '{test_persona_name}' nicht laden")
                    results["yaml_personas"] = {"status": "warnung", "details": "Konnte YAML-Persona nicht laden"}
        except ImportError as e:
            results["yaml_personas"] = {"status": "fehler", "details": f"Import-Fehler: {e}"}
            print(Fore.RED + f"  ❌ YAML-Persona-Modul konnte nicht importiert werden: {e}")
            logger.error(f"YAML-Persona-Modul Import-Fehler: {e}")
        except Exception as e:
            results["yaml_personas"] = {"status": "fehler", "details": str(e)}
            print(Fore.RED + f"  ❌ YAML-Persona-Test fehlgeschlagen: {e}")
            logger.error(f"YAML-Persona-Test fehlgeschlagen: {e}", exc_info=True)

        # Zusammenfassung
        print(Fore.YELLOW + "\n--- Selftest-Zusammenfassung ---")
        all_ok = all(r["status"] == "ok" for r in results.values())
        if all_ok:
            print(Fore.GREEN + "✅ Alle Tests erfolgreich bestanden. NavyYard ist bereit.")
        else:
            warnings = sum(1 for r in results.values() if r["status"] == "warnung")
            errors = sum(1 for r in results.values() if r["status"] == "fehler")
            if errors > 0:
                print(Fore.RED + f"❌ {errors} Fehler und {warnings} Warnungen gefunden.")
            else:
                print(Fore.YELLOW + f"⚠️ {warnings} Warnungen gefunden, aber keine kritischen Fehler.")
                print(Fore.GREEN + "✅ NavyYard sollte funktionsfähig sein.")
                
    except Exception as e:
        print(Fore.RED + f"❌ Kritischer Fehler im Selftest: {e}")
        logger.critical(f"Kritischer Fehler im Selftest: {e}", exc_info=True)
        print(Fore.RED + traceback.format_exc())
