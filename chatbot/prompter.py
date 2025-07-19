# abby_chatbot/chatbot/prompter.py
"""
PromptBuilder für Abby Chatbot
Baut Prompts dynamisch basierend auf Persona, Gesprächsverlauf und Uhrzeit

Dieses Modul ist verantwortlich für die Erstellung strukturierter Prompts für das
Sprachmodell. Es kombiniert die aktuelle Persona, den Konversationsverlauf und
Kontextinformationen wie die aktuelle Uhrzeit, um einen vollständigen Prompt zu erstellen.

Der PromptBuilder verwendet das ChatML-Format, das von den meisten modernen Sprachmodellen
unterstützt wird und eine klare Trennung zwischen System-, Benutzer- und Assistenten-
Nachrichten ermöglicht.
"""
from datetime import datetime
import logging
from chatbot.error_handler import ChatbotError

# Logger für dieses Modul
logger = logging.getLogger("PromptBuilder")

class PromptError(ChatbotError):
    """Fehler bei der Erstellung von Prompts."""
    pass

class PromptBuilder:
    """
    Erstellt strukturierte Prompts für das Sprachmodell.
    
    Diese Klasse ist verantwortlich für die Erstellung von Prompts im ChatML-Format,
    die an das Sprachmodell gesendet werden. Sie kombiniert die Persona-Definition,
    den Konversationsverlauf und Kontextinformationen wie die aktuelle Uhrzeit.
    """
    def __init__(self, persona_text="Du bist ein neutraler Assistent."):
        """
        Initialisiert den PromptBuilder mit einem Persona-Text.
        
        Args:
            persona_text (str): Der Text, der die Persona des Chatbots definiert
                                und als System-Prompt verwendet wird
                                
        Raises:
            PromptError: Bei Problemen mit dem Persona-Text
        """
        try:
            if not isinstance(persona_text, str):
                logger.warning(f"Ungültiger Persona-Text-Typ: {type(persona_text)}, konvertiere zu String")
                persona_text = str(persona_text)
                
            # Stelle sicher, dass der Text nicht leer ist
            if not persona_text.strip():
                logger.warning("Leerer Persona-Text, verwende Standard")
                persona_text = "Du bist ein neutraler Assistent."
                
            self.system_prompt = persona_text.strip()
            logger.debug(f"PromptBuilder initialisiert mit Persona: {self.system_prompt[:50]}...")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des PromptBuilders: {e}")
            self.system_prompt = "Du bist ein neutraler Assistent."
            raise PromptError(f"Fehler bei der Initialisierung des PromptBuilders: {e}")

    def build(self, history, user_input):
        """
        Erstellt einen vollständigen Prompt im ChatML-Format.
        
        Diese Methode kombiniert den System-Prompt (Persona), den Konversationsverlauf
        und die aktuelle Benutzereingabe zu einem strukturierten Prompt im ChatML-Format.
        Sie fügt auch Kontextinformationen wie die aktuelle Uhrzeit hinzu.
        
        Args:
            history (list): Liste von Tupeln (user_input, bot_answer) aus dem Gedächtnis
            user_input (str): Die aktuelle Eingabe des Benutzers
            
        Returns:
            list: Eine Liste von Nachrichten im ChatML-Format, die an das Modell gesendet werden kann
            
        Raises:
            PromptError: Bei Problemen mit der Prompt-Erstellung
        """
        try:
            # Validiere Eingaben
            if not isinstance(history, list):
                logger.warning(f"Ungültiger Verlaufstyp: {type(history)}, verwende leere Liste")
                history = []
                
            if not isinstance(user_input, str):
                logger.warning(f"Ungültiger Eingabetyp: {type(user_input)}, konvertiere zu String")
                user_input = str(user_input)
                
            # Aktuelle Zeit hinzufügen
            try:
                now = datetime.now().strftime("%H:%M Uhr")
                time_note = f"Es ist aktuell {now}."
            except Exception as e:
                logger.warning(f"Fehler beim Formatieren der Zeit: {e}")
                time_note = "Die aktuelle Uhrzeit ist unbekannt."

            # Erstelle Nachrichtenliste
            messages = [
                {"role": "system", "content": f"{self.system_prompt}\n{time_note}"},
            ]

            # Implementiere Token-Zählung-Schätzung
            def estimate_tokens(text):
                # Grobe Schätzung: 1 Token ≈ 4 Zeichen für englischen Text
                # Für andere Sprachen kann das Verhältnis variieren
                return len(text) // 4
            
            # Bestimme, ob wir den vollen Kontext benötigen basierend auf der Anfrage
            simple_query = len(user_input) < 50 and "?" in user_input
            
            # Für einfache Fragen brauchen wir möglicherweise nicht viel Verlauf
            if simple_query and len(history) > 2:
                logger.info("Einfache Frage erkannt, reduziere Verlauf")
                history = history[-2:]  # Behalte nur die letzten 2 Austausche
            
            # Berechne den verfügbaren Token-Platz für den Verlauf
            system_tokens = estimate_tokens(messages[0]["content"])
            user_input_tokens = estimate_tokens(user_input)
            
            # Reserviere Platz für die Antwort und einen Puffer
            max_tokens = 4000  # Kontextfenster abzüglich Platz für die Antwort
            available_tokens = max_tokens - system_tokens - user_input_tokens - 500  # 500 Token Puffer
            
            # Füge Verlauf hinzu, beginnend mit den neuesten Einträgen
            history_messages = []
            used_tokens = 0
            
            for i, (user_msg, bot_msg) in enumerate(reversed(history)):
                try:
                    if not isinstance(user_msg, str):
                        user_msg = str(user_msg)
                    if not isinstance(bot_msg, str):
                        bot_msg = str(bot_msg)
                    
                    user_tokens = estimate_tokens(user_msg)
                    bot_tokens = estimate_tokens(bot_msg)
                    pair_tokens = user_tokens + bot_tokens
                    
                    # Prüfe, ob dieses Paar noch in den verfügbaren Platz passt
                    if used_tokens + pair_tokens <= available_tokens:
                        history_messages.insert(0, {"role": "user", "content": user_msg})
                        history_messages.insert(1, {"role": "assistant", "content": bot_msg})
                        used_tokens += pair_tokens
                    else:
                        logger.info(f"Verlauf gekürzt auf {i} von {len(history)} Einträgen wegen Token-Limit")
                        break
                except Exception as e:
                    logger.warning(f"Fehler beim Hinzufügen des Verlaufseintrags {i}: {e}")
                    # Überspringe diesen Eintrag, aber breche nicht ab
            
            # Füge den optimierten Verlauf zu den Nachrichten hinzu
            messages.extend(history_messages)

            # Füge aktuelle Benutzereingabe hinzu
            messages.append({"role": "user", "content": user_input})
            
            # Validiere Gesamtgröße des Prompts
            total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)
            logger.info(f"Geschätzte Token-Anzahl für Prompt: {total_tokens}")
            
            if total_tokens > max_tokens:
                logger.warning(f"Prompt könnte zu groß sein: ~{total_tokens} Token")
            
            return messages
            
        except Exception as e:
            logger.error(f"Fehler bei der Prompt-Erstellung: {e}")
            # Fallback auf minimalen Prompt
            return [
                {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                {"role": "user", "content": user_input}
            ]
