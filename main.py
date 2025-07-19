
# abby_chatbot/main.py
"""
NavyYard Chatbot - Startpunkt
Autor: Du ;)
Beschreibung: Einstiegspunkt für den NavyYard-KI-Chatbot (Bot V3)

Dieses Modul ist der Haupteinstiegspunkt für den NavyYard-Chatbot. Es setzt
wichtige Umgebungsvariablen für die GPU-Beschleunigung und initialisiert
den Chatbot.^

Die Hauptfunktion dieses Moduls:
1. Setzt die LLAMA_CUBLAS-Umgebungsvariable für GPU-Unterstützung
2. Importiert und initialisiert die AbbyBot-Klasse
3. Startet die Hauptschleife des Chatbots

Dieses Modul sollte direkt ausgeführt werden, um den Chatbot zu starten.
"""
import os
# Setze die Umgebungsvariable, BEVOR irgendetwas von llama_cpp importiert wird.
os.environ["LLAMA_CUBLAS"] = "1"

from chatbot.bot import AbbyBot

def main():
    """
    Hauptfunktion zum Starten des NavyYard-Chatbots.
    
    Diese Funktion initialisiert eine Instanz der AbbyBot-Klasse und
    startet die Hauptschleife des Chatbots. Sie wird aufgerufen, wenn
    das Skript direkt ausgeführt wird.
    
    Die Funktion:
    1. Erstellt eine neue Instanz des Chatbots
    2. Ruft die run()-Methode auf, die die interaktive Schleife startet
    """
    bot = AbbyBot()
    bot.run()

if __name__ == "__main__":
    main()