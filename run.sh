#!/bin/bash
# run.sh – Startet Abby Chatbot inkl. virtueller Umgebung und Abhängigkeiten
# ID: RUNSH-FINAL-BULLETPROOF-01 (v3 - mit System-Check)
# Prüft Systemabhängigkeiten, kompiliert llama-cpp-python mit GPU-Support und installiert dann den Rest.

set -e  # Skript bricht bei Fehlern ab

# --- System-Check: Prüfen, ob wichtige Build-Tools installiert sind ---
REQUIRED_TOOLS="cmake autoconf"
for tool in $REQUIRED_TOOLS; do
    if ! command -v $tool &> /dev/null; then
        echo "❌ FEHLER: Das wichtige Build-Tool '$tool' wurde nicht gefunden."
        echo "Bitte installiere es mit: sudo apt-get install -y build-essential cmake autoconf"
        exit 1
    fi
done
echo "✅ System-Check erfolgreich. Alle Build-Tools sind vorhanden."


VENV_DIR=".venv"

# Prüfen, ob die virtuelle Umgebung bereits existiert.
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Keine virtuelle Umgebung gefunden. Führe komplette Erstinstallation durch..."
    
    # 1. Virtuelle Umgebung erstellen und aktivieren
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # 2. Pip aktualisieren
    echo "📚 Aktualisiere pip..."
    python3 -m pip install --upgrade pip
    
    # 3. WICHTIG: Installiere zuerst llama-cpp-python mit GPU-Support
    echo "🛠️ Installiere llama-cpp-python mit GPU-Support (dies dauert einen Moment)..."
    CMAKE_ARGS="-DGGML_CUDA=on" python3 -m pip install --no-cache-dir --no-binary :all: llama-cpp-python
    
    # 4. Installiere die restlichen Abhängigkeiten aus der bereinigten Datei
    echo "📚 Installiere restliche Abhängigkeiten..."
    python3 -m pip install -r requirements.txt
    
    # TTS-related dependencies have been removed as part of the TTS Complete Removal feature
    
    echo "✅ Setup abgeschlossen. Zukünftige Starts werden schneller sein."

else
    # Wenn die Umgebung existiert, einfach nur aktivieren.
    echo "✅ Vorhandene virtuelle Umgebung gefunden. Aktiviere sie..."
    source "$VENV_DIR/bin/activate"
fi

# Bot starten (passiert bei jedem Ausführen)
echo "🚀 Starte Abby... Jetzt mit voller GPU-Power!"
python3 main.py
