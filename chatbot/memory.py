# abby_chatbot/chatbot/memory.py
"""
Gedächtnis-Modul für Abby Chatbot
Speichert und liefert Chatverlauf (Kurzzeitgedächtnis)
Langzeit optional erweiterbar (z.B. DB, Vektorsuche)

Dieses Modul implementiert das Kurzzeitgedächtnis des Chatbots, das für die
Aufrechterhaltung des Konversationskontexts verantwortlich ist. Es speichert
eine begrenzte Anzahl von Nachrichtenpaaren (Benutzer-Eingabe und Bot-Antwort)
und stellt diese für die Erstellung von Prompts zur Verfügung.

Das Modul ist bewusst einfach gehalten, um später durch komplexere Implementierungen
(z.B. mit Datenbank-Persistenz oder Vektorsuche) ersetzt werden zu können, ohne
die Schnittstelle zu ändern.
"""
from collections import deque
import logging
from chatbot.error_handler import ChatbotError

# Logger für dieses Modul
logger = logging.getLogger("Memory")

class MemoryError(ChatbotError):
    """Fehler bei der Verwaltung des Konversationsgedächtnisses."""
    pass

class Memory:
    """
    Implementiert das Kurzzeitgedächtnis des Chatbots.
    
    Diese Klasse speichert eine begrenzte Anzahl von Nachrichtenpaaren
    (Benutzer-Eingabe und Bot-Antwort) in einer Ringpuffer-Struktur.
    Wenn die maximale Länge erreicht ist, werden die ältesten Einträge
    automatisch entfernt.
    """
    def __init__(self, maxlen=10):
        """
        Initialisiert das Gedächtnis mit einer maximalen Länge.
        
        Args:
            maxlen (int): Maximale Anzahl der zu speichernden Nachrichtenpaare
            
        Raises:
            MemoryError: Wenn maxlen ungültig ist
        """
        try:
            # Validiere maxlen
            if not isinstance(maxlen, int):
                logger.warning(f"Ungültiger maxlen-Typ: {type(maxlen)}, verwende 10")
                maxlen = 10
            if maxlen <= 0:
                logger.warning(f"Ungültiger maxlen-Wert: {maxlen}, verwende 10")
                maxlen = 10
                
            self.history = deque(maxlen=maxlen)  # Kurzzeitgedächtnis
            logger.debug(f"Memory initialisiert mit maxlen={maxlen}")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des Gedächtnisses: {e}")
            # Fallback auf Standardwert
            self.history = deque(maxlen=10)
            raise MemoryError(f"Fehler bei der Initialisierung des Gedächtnisses: {e}")

    def add_entry(self, user_input, bot_answer):
        """
        Fügt ein neues Nachrichtenpaar zum Verlauf hinzu.
        
        Args:
            user_input (str): Die Eingabe des Benutzers
            bot_answer (str): Die Antwort des Bots
            
        Raises:
            MemoryError: Bei Problemen mit den Eingabedaten
        """
        try:
            # Validiere Eingaben
            if not isinstance(user_input, str):
                user_input = str(user_input)
                logger.warning(f"Nicht-String Benutzereingabe konvertiert: {type(user_input)}")
                
            if not isinstance(bot_answer, str):
                bot_answer = str(bot_answer)
                logger.warning(f"Nicht-String Bot-Antwort konvertiert: {type(bot_answer)}")
                
            # Trimme sehr lange Eingaben/Antworten, um Speicherprobleme zu vermeiden
            max_length = 10000  # Vernünftiges Maximum für Textlänge
            if len(user_input) > max_length:
                user_input = user_input[:max_length] + "... [gekürzt]"
                logger.warning(f"Benutzereingabe gekürzt (Länge: {len(user_input)})")
                
            if len(bot_answer) > max_length:
                bot_answer = bot_answer[:max_length] + "... [gekürzt]"
                logger.warning(f"Bot-Antwort gekürzt (Länge: {len(bot_answer)})")
                
            self.history.append((user_input, bot_answer))
            logger.debug(f"Eintrag hinzugefügt, aktuelle Verlaufslänge: {len(self.history)}")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen eines Eintrags: {e}")
            raise MemoryError(f"Fehler beim Speichern des Gesprächsverlaufs: {e}")

    def get_recent(self):
        """
        Gibt den aktuellen Verlauf als Liste zurück.
        
        Returns:
            list: Liste von Tupeln (user_input, bot_answer)
        """
        try:
            return list(self.history)
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Verlaufs: {e}")
            return []  # Leere Liste als Fallback

    def clear(self):
        """
        Löscht den gesamten Verlauf.
        """
        try:
            self.history.clear()
            logger.debug("Verlauf gelöscht")
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Verlaufs: {e}")
            # Erstelle neuen leeren Verlauf als Fallback
            self.history = deque(maxlen=self.history.maxlen)
