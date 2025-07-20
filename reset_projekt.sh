#!/bin/bash
# ID: ABBY-PROJECT-RESET-01
# Protokoll: Setzt das AKTUELLE Verzeichnis zurück und initialisiert es als GPU-fähiges Llama.cpp Projekt.
# Version 6: Löscht ein bestehendes .venv, um einen sauberen Neustart zu garantieren.

# --- Farben für mein Labor-Terminal ---
C_CYAN='\033[0;36m'
C_GREEN='\033[0;32m'
C_RED='\033[0;31m'
C_YELLOW='\033[1;33m'
C_NC='\033[0m' # No Color

# --- Hilfsfunktionen für meine Berichte ---
msg() {
    echo -e "${C_CYAN}INFO: $1${C_NC}"
}
success() {
    echo -e "${C_GREEN}ERFOLG: $1${C_NC}"
}
error() {
    echo -e "${C_RED}FEHLER: $1${C_NC}" >&2
    exit 1
}
print_warning() {
    echo -e "${C_YELLOW}WARNUNG: $1${C_NC}"
}

# --- Schritt 1: Tatort-Inspektion und -Säuberung ---
if [ -d ".venv" ]; then
  print_warning "Ein Labor (.venv) existiert bereits. Protokoll 'Verbrannte Erde' wird eingeleitet..."
  rm -rf .venv
  success "Altes Labor wurde dekontaminiert (gelöscht)."
fi

REQS_FILE="requirements.txt"

# --- Schritt 2: Labor aufbauen (venv erstellen) ---
msg "Riegel den Tatort ab... Baue Labor (.venv) im aktuellen Verzeichnis auf."
python3 -m venv .venv
if [ ! -f ".venv/bin/activate" ]; then
    error "Konnte die virtuelle Umgebung nicht erstellen. Labor kontaminiert."
fi
success "Virtuelle Umgebung '.venv' ist bereit."

# --- Schritt 3: Spezialausrüstung installieren ---
msg "Aktiviere die Laborumgebung und installiere die Ausrüstung..."
source .venv/bin/activate

# Zuerst unsere spezielle GPU-Version von llama-cpp-python
msg "Installiere primäres Beweismittel (llama-cpp-python mit GPU-Support)..."
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python==0.2.28 &>/dev/null
# Erfolgskontrolle
python -c "from llama_cpp import llama_cpp" &>/dev/null
if [ $? -ne 0 ]; then
    error "Installation von llama-cpp-python fehlgeschlagen!"
fi
success "Spezialausrüstung 'llama-cpp-python' wurde erfolgreich installiert."

# Dann die restlichen Abhängigkeiten, FALLS eine 'requirements.txt' existiert
if [ -f "$REQS_FILE" ]; then
    # Erstelle eine temporäre, saubere Anforderungsdatei
    CLEAN_REQS_FILE=$(mktemp)
    # Filtere Kommentare, leere Zeilen und unser Spezialpaket heraus.
    grep -iv "llama-cpp-python" "$REQS_FILE" | grep -vE '^\s*#|^\s*$' > "$CLEAN_REQS_FILE"

    # Installiere nur, wenn nach dem Filtern noch etwas übrig ist.
    if [ -s "$CLEAN_REQS_FILE" ]; then
        msg "'requirements.txt' gefunden. Installiere weitere Beweismittel..."
        pip install -r "$CLEAN_REQS_FILE"
        if [ $? -ne 0 ]; then
            print_warning "Einige zusätzliche Anforderungen konnten nicht installiert werden. Bitte überprüfe die 'requirements.txt' und die pip-Fehlermeldungen."
        else
            success "Zusätzliche Anforderungen wurden erfolgreich installiert."
        fi
    else
        msg "Keine weiteren Anforderungen in 'requirements.txt' zu installieren."
    fi
    # Räume die temporäre Datei auf. Keine Spuren hinterlassen.
    rm "$CLEAN_REQS_FILE"
else
    msg "Keine 'requirements.txt' gefunden. Überspringe diesen Schritt."
fi

# --- Abschlussbericht ---
echo -e "\n"
success "======================================================================="
success "  >>> PROJEKT ERFOLGREICH ZURÜCKGESETZT & INITIALISIERT <<<"
msg "Das Labor ist sauber und einsatzbereit. Um es zu benutzen:"
print_warning "  Aktiviere einfach die Umgebung: source .venv/bin/activate"
success "======================================================================="
