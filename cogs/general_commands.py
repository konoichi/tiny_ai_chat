# cogs/general_commands.py

import discord
from discord.ext import commands
import logging

# Dies ist der Cog für alle allgemeinen und nützlichen Befehle,
# die nicht direkt mit der KI-Modellverwaltung zu tun haben.

class GeneralCommandsCog(commands.Cog):
    def __init__(self, bot):
        """
        Der Konstruktor. Wir speichern die bot-Instanz.
        """
        self.bot = bot

    @commands.command(name='say', help='Lässt den Bot einen Text sagen (für Debugging).')
    @commands.is_owner() # Nur der Bot-Owner kann diesen Befehl nutzen
    async def say(self, ctx, *, text: str):
        """
        Der !say-Befehl. Nützlich für Tests.
        Löscht die ursprüngliche Nachricht, damit der Chat sauber bleibt.
        """
        logging.info(f"Executing !say command with text: {text}")
        await ctx.message.delete()
        await ctx.send(text)

    @commands.command(name='reset', help='Setzt den Chatverlauf des Bots zurück.')
    async def reset(self, ctx):
        """
        Löscht das Gedächtnis des Bots für den aktuellen Kanal.
        """
        logging.info("Executing !reset command.")
        self.bot.memory.clear()
        # Wichtig: Den System-Prompt nach dem Löschen wiederherstellen!
        self.bot.memory.set_system_prompt(self.bot.persona_manager.get_system_prompt())
        await ctx.send("Mein Kurzzeitgedächtnis wurde soeben gelöscht. Worüber wollten wir sprechen?")

    @commands.command(name='ping', help='Überprüft die Latenz des Bots.')
    async def ping(self, ctx):
        """
        Zeigt die aktuelle Latenz zum Discord-Server an.
        """
        latency = self.bot.latency * 1000  # in Millisekunden
        await ctx.send(f"Pong! Meine Reaktionszeit beträgt {latency:.2f} ms. Ziemlich schnell, was?")

    @commands.command(name='help', help='Zeigt diese Hilfenachricht an.')
    async def help_command(self, ctx):
        """
        Ein neuer, schönerer !help-Befehl, der Discord Embeds nutzt.
        """
        embed = discord.Embed(
            title="Hilfe-Menü",
            description="Hier sind alle Befehle, die ich verstehe:",
            color=discord.Color.dark_purple() # Gothic, natürlich.
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        # Füge Befehle für jeden Cog hinzu
        for cog_name, cog in self.bot.cogs.items():
            command_list = []
            for command in cog.get_commands():
                if not command.hidden: # Versteckte Befehle ignorieren
                    command_list.append(f"`{self.bot.command_prefix}{command.name}` - {command.help}")
            
            if command_list:
                 # Ersetze Unterstriche im Cog-Namen durch Leerzeichen für eine schönere Anzeige
                cog_display_name = cog_name.replace('_', ' ').title()
                embed.add_field(
                    name=f"⚙️ {cog_display_name}",
                    value="\n".join(command_list),
                    inline=False
                )
        
        embed.set_footer(text="Gothic-Boss-Bot | Refactoring in Progress")
        await ctx.send(embed=embed)

# Die Setup-Funktion, die diesen Cog zum Bot hinzufügt
async def setup(bot):
    await bot.add_cog(GeneralCommandsCog(bot))
