# cogs/system_commands.py

import discord
from discord.ext import commands
import logging
# Hier könnten wir später weitere System-spezifische Imports hinzufügen,
# z.B. für die Hardware-Erkennung.

class SystemCommandsCog(commands.Cog, name="System & Debug"):
    """
    Dieser Cog enthält Befehle zur Überwachung, Steuerung und
    Fehlersuche des Bots.
    """
    def __init__(self, bot):
        self.bot = bot
        # Wir setzen hier Standardwerte für die Schalter, falls sie im Bot noch nicht existieren.
        # Im Idealfall werden diese in der Bot-Klasse oder einer Config initialisiert.
        self.bot.tts_enabled = getattr(bot, 'tts_enabled', False)
        self.bot.debug_mode = getattr(bot, 'debug_mode', False)

    @commands.command(name='status', help='Zeigt den aktuellen Status des Bots an.')
    async def status(self, ctx):
        """
        Gibt eine Übersicht über den aktuellen Zustand des Bots.
        """
        current_model = self.bot.model_manager.get_current_model_name() or "Keins"
        current_persona = self.bot.persona_manager.get_current_persona_name() or "Standard"
        
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="Aktives Modell", value=f"`{current_model}`", inline=True)
        embed.add_field(name="Aktive Persona", value=f"`{current_persona}`", inline=True)
        embed.add_field(name="TTS Aktiviert", value=f"`{self.bot.tts_enabled}`", inline=False)
        embed.add_field(name="Debug Modus", value=f"`{self.bot.debug_mode}`", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='tts', help='Schaltet Text-to-Speech (TTS) an oder aus.')
    @commands.is_owner()
    async def tts(self, ctx, switch: str):
        """
        Schaltet die TTS-Funktion um. Akzeptiert 'on' oder 'off'.
        """
        if switch.lower() == 'on':
            self.bot.tts_enabled = True
            await ctx.send("TTS ist jetzt **aktiviert**.")
        elif switch.lower() == 'off':
            self.bot.tts_enabled = False
            await ctx.send("TTS ist jetzt **deaktiviert**.")
        else:
            await ctx.send("Ungültige Eingabe. Bitte benutze `on` oder `off`.")
        logging.info(f"TTS enabled set to: {self.bot.tts_enabled}")

    @commands.command(name='debug', help='Schaltet den Debug-Modus an oder aus.')
    @commands.is_owner()
    async def debug(self, ctx, switch: str):
        """
        Schaltet den Debug-Modus um.
        """
        if switch.lower() == 'on':
            self.bot.debug_mode = True
            logging.getLogger().setLevel(logging.DEBUG)
            await ctx.send("Debug-Modus ist jetzt **aktiviert**. Die Konsole wird gesprächiger.")
        elif switch.lower() == 'off':
            self.bot.debug_mode = False
            # Setze den Log-Level zurück auf den Standard (z.B. INFO)
            log_level = os.getenv("LOG_LEVEL", "INFO").upper()
            logging.getLogger().setLevel(log_level)
            await ctx.send("Debug-Modus ist jetzt **deaktiviert**.")
        else:
            await ctx.send("Ungültige Eingabe. Bitte benutze `on` oder `off`.")
        logging.info(f"Debug mode set to: {self.bot.debug_mode}")
        
    # Die Befehle !hardware und !stream könnten hier ebenfalls hinzugefügt werden,
    # sobald ihre Logik aus den alten Dateien extrahiert wurde.

# Die Setup-Funktion, die diesen Cog zum Bot hinzufügt
async def setup(bot):
    await bot.add_cog(SystemCommandsCog(bot))
