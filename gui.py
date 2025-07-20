# gui.py
"""
Version: 4.0.0
------------------------------
ID: NAVYYARD-GRADIO-UI-V4-STREAMING-01
Beschreibung: Die finale, web-basierte Kommandozentrale für den NavyYard-Chatbot.
FEATURE 1: Implementiert Live-Streaming der KI-Antworten. Der Text erscheint
jetzt Wort für Wort im Chatfenster, anstatt am Ende als ganzer Block.
FEATURE 2: Implementiert einen Audio-Bericht für den Selftest. Wenn TTS
aktiviert ist, wird das Ergebnis des Selftests vorgelesen.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""
import gradio as gr
from chatbot.bot import AbbyBot
from chatbot import bot_model_commands as bmc
import time
import io
import sys
from contextlib import redirect_stdout

# --- Initialisierung ---
print("Initialisiere AbbyBot für die Gradio-Oberfläche...")
bot = AbbyBot()
print("AbbyBot initialisiert.")

# --- Kernfunktionen für die GUI ---

def chat_response_generator(message, chat_history, tts_enabled):
    """
    Eine Generator-Funktion, die die KI-Antwort streamt.
    Sie 'yielded' den aktualisierten Chat-Verlauf nach jedem neuen Wort.
    """
    # Füge die User-Nachricht sofort zum Verlauf hinzu.
    chat_history.append((message, ""))
    
    full_response = ""
    # Rufe die neue Streaming-Methode im Bot auf.
    for response_part in bot.process_llm_request_stream(message):
        full_response = response_part # Die Methode liefert den bisher kompletten Text
        chat_history[-1] = (message, full_response)
        yield "", chat_history
    
    # Nachdem der Stream beendet ist, spiele den kompletten Text ab, wenn TTS aktiviert ist.
    if tts_enabled and bot.tts_manager:
        bot.tts_manager.speak(full_response)

def change_persona(persona_name):
    """Wird aufgerufen, wenn eine neue Persona ausgewählt wird."""
    bot.handle_persona_command(f"!persona {persona_name}")
    return f"Persona zu '{persona_name}' gewechselt.", []

def change_model(model_name):
    """Wird aufgerufen, wenn ein neues Modell ausgewählt wird."""
    try:
        idx = [m.name for m in bmc.model_list].index(model_name) + 1
        bot.handle_model_command(f"!model {idx}")
        return f"Modell zu '{model_name}' gewechselt.", []
    except ValueError:
        return "Fehler: Modell nicht in der Liste gefunden.", []

def reset_chat():
    """Wird aufgerufen, wenn der Reset-Button geklickt wird."""
    bot.handle_reset_command("!reset")
    return "Chat zurückgesetzt.", []

def run_bot_command(command_func, *args):
    """Leitet die Konsolenausgabe einer Bot-Funktion in einen String um."""
    f = io.StringIO()
    with redirect_stdout(f):
        command_func(*args)
    return f.getvalue()

def run_selftest_with_audio(tts_enabled):
    """Führt den Selftest aus und gibt optional einen Audio-Bericht aus."""
    # Fange den Text-Report ab
    report_text = run_bot_command(bot.handle_selftest_command, "!selftest")
    
    # Wenn TTS aktiviert ist, generiere und spreche eine Zusammenfassung.
    if tts_enabled and bot.tts_manager:
        summary = "Selftest initiated. "
        if "Alle kritischen Tests erfolgreich" in report_text:
            summary += "All systems operational. NavyYard is ready."
        else:
            summary += "Warning. At least one test failed. Please check the logs."
        bot.tts_manager.speak(summary)
        
    return report_text

def get_status_report():
    return run_bot_command(bot.display_status)

def get_hardware_report():
    return run_bot_command(bot.display_hardware_info)

def run_benchmark():
    return run_bot_command(bot.handle_benchmark_command, "!benchmark")

def get_available_personas():
    return bot.persona_manager.list_available_personas()

def get_available_models():
    return [model.name for model in bmc.model_list]

# --- Aufbau der Gradio-Oberfläche ---

with gr.Blocks(theme=gr.themes.Soft(primary_hue="slate", secondary_hue="blue"), title="NavyYard Chatbot") as demo:
    gr.Markdown("# 💬 NavyYard Kommandozentrale")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Steuerung")
            persona_dropdown = gr.Dropdown(label="Aktive Persona", choices=get_available_personas(), value=bot.persona_manager.get_current_name())
            model_dropdown = gr.Dropdown(label="Aktives Modell", choices=get_available_models(), value=bmc.active_model.name if bmc.active_model else "Keins geladen")
            tts_checkbox = gr.Checkbox(label="🔊 TTS-Ausgabe aktivieren", value=False)
            reset_button = gr.Button("🧹 Chat zurücksetzen")
            status_display = gr.Textbox(label="Status", interactive=False, lines=2)

            with gr.Accordion("🛠️ Diagnose-Werkzeuge", open=False):
                with gr.Row():
                    status_button = gr.Button("Status")
                    hardware_button = gr.Button("Hardware")
                with gr.Row():
                    selftest_button = gr.Button("Selftest")
                    benchmark_button = gr.Button("Benchmark")
                diagnose_output = gr.Markdown(label="Diagnose-Ausgabe")

        with gr.Column(scale=4):
            chatbot = gr.Chatbot(label="Chat", height=500)
            msg = gr.Textbox(label="Deine Nachricht...", show_label=False, placeholder="Schreibe hier deine Nachricht und drücke Enter...")
            clear = gr.ClearButton([msg, chatbot])

    # --- Event-Handler ---
    msg.submit(chat_response_generator, [msg, chatbot, tts_checkbox], [msg, chatbot])
    persona_dropdown.change(change_persona, inputs=[persona_dropdown], outputs=[status_display, chatbot])
    model_dropdown.change(change_model, inputs=[model_dropdown], outputs=[status_display, chatbot])
    reset_button.click(reset_chat, outputs=[status_display, chatbot])
    
    status_button.click(get_status_report, outputs=[diagnose_output])
    hardware_button.click(get_hardware_report, outputs=[diagnose_output])
    # Der Selftest-Button übergibt jetzt den Status der TTS-Checkbox.
    selftest_button.click(run_selftest_with_audio, inputs=[tts_checkbox], outputs=[diagnose_output])
    benchmark_button.click(run_benchmark, outputs=[diagnose_output])

# --- Start der Anwendung ---
if __name__ == "__main__":
    print("Starte Gradio-Oberfläche...")
    demo.launch(share=True)
