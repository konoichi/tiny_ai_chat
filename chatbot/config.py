# chatbot/config.py
"""
Konfigurationsmodul für den Abby Chatbot

Dieses Modul stellt globale Einstellungen und Konfigurationsparameter für den
gesamten Chatbot bereit. Es verwendet eine Singleton-Klasse (SETTINGS), um
konsistente Einstellungen über alle Module hinweg zu gewährleisten.

Die SETTINGS-Klasse kann zur Laufzeit aktualisiert werden, z.B. wenn der Benutzer
den Debug-Modus aktiviert oder deaktiviert.
"""

class SETTINGS:
    """
    Singleton-Klasse für globale Einstellungen des Chatbots.
    
    Diese Klasse speichert globale Konfigurationsparameter, die von verschiedenen
    Teilen des Systems verwendet werden. Sie bietet Klassenmethoden zum Setzen
    und Abfragen dieser Parameter.
    
    Attributes:
        debug (bool): Flag für den Debug-Modus
    """
    debug = False

    @classmethod
    def set_debug(cls, value: bool):
        """
        Setzt den Debug-Modus.
        
        Args:
            value (bool): True, um den Debug-Modus zu aktivieren, False, um ihn zu deaktivieren
        """
        cls.debug = value

    @classmethod
    def is_debug(cls) -> bool:
        """
        Gibt den aktuellen Status des Debug-Modus zurück.
        
        Returns:
            bool: True, wenn der Debug-Modus aktiviert ist, sonst False
        """
        return cls.debug
