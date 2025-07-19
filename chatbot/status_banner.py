"""
/chatbot/status_banner.py
Version: 1.0.0
------------------------------
Status-Banner für den NavyYard Chatbot

Dieses Modul stellt eine Komponente bereit, die ein formatiertes Status-Banner
anzeigt, das Informationen über das aktive Modell, den Hardware-Modus und die
aktive Persona enthält. Das Banner wird beim Start und nach Modellwechseln angezeigt.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

import logging
from colorama import Fore, Style, Back
from typing import Dict, Any, Optional

# Logger für dieses Modul
logger = logging.getLogger("StatusBanner")

class StatusBanner:
    """
    Komponente zur Anzeige eines formatierten Status-Banners.
    
    Diese Klasse generiert und zeigt ein formatiertes Banner an, das Informationen
    über das aktive Modell, den Hardware-Modus und die aktive Persona enthält.
    Das Banner wird beim Start und nach Modellwechseln angezeigt.
    
    Attributes:
        bot: Referenz auf die Bot-Instanz
        banner_width (int): Breite des Banners in Zeichen
        separator_char (str): Zeichen für die Trennlinie
    """
    
    def __init__(self, bot, banner_width: int = 50, separator_char: str = "="):
        """
        Initialisiert das StatusBanner.
        
        Args:
            bot: Referenz auf die Bot-Instanz
            banner_width (int): Breite des Banners in Zeichen
            separator_char (str): Zeichen für die Trennlinie
        """
        self.bot = bot
        self.banner_width = banner_width
        self.separator_char = separator_char
        
    def generate_banner(self) -> str:
        """
        Generiert das Status-Banner basierend auf dem aktuellen Zustand.
        
        Returns:
            str: Das generierte Banner als formatierter String
        """
        # Hole Modell-Informationen
        from . import bot_model_commands as bmc
        model_name = "Nicht geladen"
        if bmc.active_model:
            model_name = bmc.active_model.name
            
        # Hole Hardware-Informationen
        hardware_mode = "UNKNOWN"
        gpu_layers = 0
        if hasattr(self.bot.model, "get_hardware_info"):
            hardware_info = self.bot.model.get_hardware_info()
            hardware_mode = hardware_info.get("mode", "UNKNOWN")
            gpu_layers = hardware_info.get("gpu_layers", 0)
            
        # Hole Persona-Informationen
        persona_name = self.bot.persona_manager.get_current_name()
        
        # Erstelle Banner
        separator = self.separator_char * self.banner_width
        title = "Abby Chatbot - Einsatzbereit"
        
        # Zentriere den Titel
        padding = (self.banner_width - len(title)) // 2
        title_line = self.separator_char * padding + title + self.separator_char * (self.banner_width - padding - len(title))
        
        # Erstelle Banner-Zeilen
        lines = [
            separator,
            title_line,
            separator,
            f"- Aktives Modell : {model_name}"
        ]
        
        # Hardware-Modus-Zeile
        if hardware_mode == "GPU":
            lines.append(f"- Betriebsmodus : GPU ({gpu_layers} Layer)")
        else:
            lines.append(f"- Betriebsmodus : {hardware_mode}")
            
        # Persona-Zeile
        lines.append(f"- Aktive Persona : {persona_name}")
        
        # Abschließende Trennlinie
        lines.append(separator)
        
        # Kombiniere zu einem String
        return "\n".join(lines)
        
    def display(self):
        """
        Zeigt das Status-Banner an.
        """
        banner = self.generate_banner()
        print(Fore.YELLOW + banner)
        
    def update(self):
        """
        Aktualisiert und zeigt das Banner erneut an.
        """
        self.display()