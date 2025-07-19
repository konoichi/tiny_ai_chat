# cogs/model_management.py

import discord
from discord.ext import commands
import logging

# Dies ist ein Cog. Ein spezialisiertes Modul für unseren Bot.
# Es kümmert sich ausschließlich um das Laden, Auflisten und Wechseln von Modellen und Personas.

class ModelManagementCog(commands.Cog):
    def __init__(self, bot):
        """
        Der Konstruktor. Hier übergeben wir die Haupt-Bot-Instanz,
        damit wir auf alles zugreifen können, was wir brauchen (z.B. model_manager).
        """
        self.bot = bot

    @commands.command(name='model', help='Verwaltet die KI-Modelle. Verfügbare Befehle: list, load, status, current.')
    async def model(self, ctx, action: str = 'status', *, model_name: str = None):
        """
        Der !model-Befehl. Lädt, listet oder zeigt den Status von Modellen.
        Fast identisch zum alten Code, aber jetzt in einer Klasse gekapselt.
        """
        logging.info(f"'model' command called with action: {action} and model_name: {model_name}")
        
        if action == 'list':
            model_list = self.bot.model_manager.get_available_models()
            if not model_list:
                await ctx.send("Keine Modelle im Cache gefunden. Führe eine Indizierung durch.")
                return

            # Erstelle eine formatierte Nachricht
            message = "```\nVerfügbare Modelle:\n"
            message += "-" * 20 + "\n"
            for model_info in model_list:
                message += f"- {model_info['name']}\n"
            message += "```"
            await ctx.send(message)

        elif action == 'load':
            if model_name is None:
                await ctx.send("Bitte gib einen Modellnamen an. `!model load <modellname>`")
                return
            
            await ctx.send(f"Lade Modell '{model_name}'... das kann einen Moment dauern.")
            try:
                success, message = await self.bot.model_manager.load_model(model_name)
                if success:
                    await ctx.send(f"Modell '{model_name}' erfolgreich geladen.")
                    await self.bot.update_status_banner()
                else:
                    await ctx.send(f"Fehler beim Laden des Modells: {message}")
            except Exception as e:
                await ctx.send(f"Ein kritischer Fehler ist aufgetreten: {e}")
                logging.error(f"Failed to load model {model_name}", exc_info=True)

        elif action in ['status', 'current']:
            current_model = self.bot.model_manager.get_current_model_name()
            if current_model:
                await ctx.send(f"Aktuell geladenes Modell: `{current_model}`")
            else:
                await ctx.send("Derzeit ist kein Modell geladen.")
        else:
            await ctx.send(f"Unbekannte Aktion '{action}'. Gültige Aktionen: list, load, status.")

    @commands.command(name='persona', help='Wechselt die Persönlichkeit des Bots.')
    async def persona(self, ctx, persona_name: str = None):
        """
        Der !persona-Befehl. Wechselt die aktive Persönlichkeit.
        """
        if persona_name is None:
            # Liste verfügbare Personas auf, wenn kein Name angegeben ist
            personas = self.bot.persona_manager.get_available_personas()
            if not personas:
                await ctx.send("Keine Personas gefunden.")
                return
            
            message = "```\nVerfügbare Personas:\n"
            message += "-" * 20 + "\n"
            for p_name in personas:
                message += f"- {p_name}\n"
            message += "```"
            await ctx.send(message)
            return

        logging.info(f"Versuche, zur Persona '{persona_name}' zu wechseln.")
        try:
            success = self.bot.persona_manager.set_persona(persona_name)
            if success:
                await ctx.send(f"Persona erfolgreich zu '{persona_name}' gewechselt.")
                logging.info(f"Persona erfolgreich zu '{persona_name}' gewechselt.")
                await self.bot.update_status_banner()
            else:
                await ctx.send(f"Persona '{persona_name}' nicht gefunden.")
                logging.warning(f"Persona '{persona_name}' nicht gefunden.")
        except Exception as e:
            await ctx.send(f"Ein Fehler ist beim Wechseln der Persona aufgetreten: {e}")
            logging.error(f"Fehler beim Wechseln der Persona zu {persona_name}", exc_info=True)


# Diese Setup-Funktion ist der magische Kleber.
# Discord.py ruft sie auf, wenn wir das Cog laden.
async def setup(bot):
    await bot.add_cog(ModelManagementCog(bot))
