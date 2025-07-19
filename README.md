# 🛠️ NavyYard

Ein modularer, lokaler KI-Chatbot mit Charakter – läuft direkt auf deinem Rechner, keine Cloud, keine Gnade. Entwickelt mit Fokus auf:

* 📦 Modularität
* 🐞 Professionelles Logging & Debugging
* 🤖 Dynamische Personas
* 🧠 Kontextuelles Gedächtnis

---

## 🚀 Features

* **Streaming-Ausgabe**: Antworten Token für Token mit `!stream on/off`
* **Persona-System**: Wähle `!persona abby`, `!persona sage` etc.
* **Farbausgabe**: Bot & User in unterschiedlichen Farben (via `colorama`)
* **Kontextverlauf**: Verlauf wird speicherbar & bearbeitbar
* **Debug-Modus**: Kontrolliert die Modell-Ausgabe (`llama_perf_context_print` etc.)
* **Umweltvariable**: Debug setzt intern `LLAMA_PERF_DISABLE=0/1`
* **Selbsttest**: `selftest` prüft wichtige Komponenten
* **Modelle flexibel austauschbar**: Nutzung beliebiger GGUF-Modelle lokal mit GPU/CPU

* **Status-Banner**: Zeigt aktives Modell, Hardware-Modus und Persona beim Start und nach Änderungen
* **Hardware-Erkennung**: Automatische Erkennung und Anzeige von CPU/GPU-Modus und GPU-Layern
* **Sofortige Modellbefehle**: `!model <n>` funktioniert direkt nach dem Start ohne vorheriges `!models`
* **Optimiertes Persona-Switching**: Blitzschneller Wechsel zwischen Personas ohne Modell-Neuladung

---

## ⚙️ Installation & Nutzung

### Voraussetzungen

* Python 3.10+
* Eine NVIDIA GPU (für CUDA-beschleunigte Modelle, optional)
* `llama-cpp-python`
* Optional: `colorama`, `pyyaml`, `tqdm`


### Setup (Linux/macOS)

```bash
git clone https://dein.git.repo/navyyard.git
cd navyyard
chmod +x run.sh
./run.sh
```

Das Skript richtet eine virtuelle Umgebung ein, installiert Abhängigkeiten und startet Abby.

---

## 🧠 Architekturüberblick

```bash
navyyard/
├── chatbot/
│   ├── bot.py              # Hauptklasse AbbyBot
│   ├── model_wrapper.py    # Llama-Modell-Wrapper mit Hardware-Erkennung
│   ├── memory.py           # Einfacher In-Memory-Verlauf
│   ├── prompter.py         # Prompt-Builder für Konversation
│   ├── persona_manager.py  # Lädt Persona-Dateien aus ./personas/
│   ├── yaml_persona_manager.py # Lädt YAML-Persona-Dateien
│   ├── status_banner.py    # Status-Banner für Modell- und Hardware-Infos
│   ├── model_manager.py    # Modell-Indexierung und -Verwaltung
│   ├── model_metadata_cache.py # Cache für Modell-Metadaten
│   
│   ├── config.py           # SETTINGS & globale Flags
│   └── selftest.py         # Systemprüfung
├── config/                 # Konfigurationsdateien
│   ├── personas/           # YAML-Persona-Dateien
│   └── settings.yaml       # Globale Einstellungen
├── tests/                  # Test-Verzeichnis
│   ├── test_hardware_detection.py # Tests für Hardware-Erkennung
│   ├── test_status_banner.py # Tests für Status-Banner
│   ├── test_integration.py # Integrationstests
│   └── performance_test.py # Performance-Tests
├── requirements.txt
├── run.sh                  # Erstellt & nutzt virtuelle Umgebung
├── run_tests.sh            # Führt Tests aus
└── main.py                 # Einstiegspunkt
```

---

## 💬 Beispiel-Session

```text
🧠 Abby sagt: Frag mich was! (Aktive Persona: abby)
👤 Du: !persona sage
🔄 Persona gewechselt zu: sage
👤 Du: what time is it?
🤖 Sage: It's 02:34 AM. Shouldn't you be sleeping? 😏
👤 Du: tell me a joke
🤖 Sage: Why don't scientists trust atoms? Because they make up everything!
```

---

## 🧪 Befehle im Chat

```text
👤 !persona <name>         - Wechsle die aktive Persona
🔁 !stream on/off          - Streaming-Modus aktivieren/deaktivieren
🧹 !reset                  - Verlauf löschen
🐞 !debug on/off           - Debug-Modus aktivieren/deaktivieren
📊 !status                 - Status anzeigen
💻 !hardware               - Detaillierte Hardware-Informationen anzeigen
🔬 !benchmark              - Performance-Benchmark durchführen
💀 selftest                - Systemcheck durchführen
📦 !models [--verbose]     - Verfügbare Modelle auflisten
🔁 !model <n>              - Modell mit Index laden
📁 !model last_model       - Letztes Modell erneut laden
ℹ️  !model                 - Zeigt Infos zum aktiven Modell (inkl. RAM)

❓ !help                   - Diese Hilfe anzeigen
🚪 exit / quit             - Abby verlassen
```

---

## 📌 To-Do & Ausbauideen

### Technische Erweiterungen

* [x] 🔄 **LLM-Wechsel zur Laufzeit** (`!model <n>`, `!model last_model`)
* [ ] 💾 **Langzeitgedächtnis** (z. B. SQLite + Embedding-Suche)
* [ ] 🕒 **Auto-Persona-Switching** (zeit- oder themenbasiert)

* [ ] 🎙️ **Voice Input** (Whisper / STT)
* [ ] 🖼️ **WebUI/GUI** (Gradio, PyQt)

### Persona-System

* [x] 📄 **YAML-Rollenprofil-Logik**
  * Persönlichkeit, Stil, Vorlieben aus YAML-Dateien

  * Zentrale Steuerung & Anpassbarkeit

---

## 👨‍🔧 Für Entwickler

* Nutze `config.py` für zentrale Flags wie `debug`, `streaming` etc.
* Einfache Erweiterbarkeit durch modulare Struktur
* `prompter.py` enthält die System-Persona-Logik
* Alle Prompts/Charaktere liegen in `config/personas/*.yaml`




### Enhanced Model Management

Das erweiterte Modellmanagement bietet verbesserte Funktionen für die Verwaltung und Überwachung von KI-Modellen:

* **Status-Banner**: Zeigt wichtige Informationen zum aktuellen Zustand des Chatbots an:
  * Aktives Modell
  * Hardware-Modus (CPU/GPU)
  * Anzahl der GPU-Layer (falls im GPU-Modus)
  * Aktive Persona
  * Wird beim Start und nach Änderungen automatisch angezeigt

* **Hardware-Erkennung**:
  * Automatische Erkennung des Hardware-Modus (CPU/GPU)
  * Bestimmung der Anzahl der GPU-Layer
  * Erkennung von GPU-Fallbacks (wenn GPU angefordert, aber CPU verwendet wird)
  * Caching des Hardware-Status für verbesserte Performance

* **Modell-Vorindexierung**:
  * Sofortige Verfügbarkeit von Modellbefehlen ohne vorherige Indexierung
  * Schnellerer Zugriff auf Modelle durch Caching
  * Persistente Speicherung des zuletzt verwendeten Modells

* **Optimiertes Persona-Switching**:
  * Blitzschneller Wechsel zwischen Personas ohne Modell-Neuladung
  * Aktualisierung nur der relevanten Komponenten (Prompt-Template)
  * Automatische Aktualisierung des Status-Banners nach Persona-Wechsel

* **Zuverlässige GPU-Konfiguration**:
  * Explizite Konfiguration der GPU-Einstellungen bei jedem Modellwechsel
  * Überprüfung der korrekten Anwendung der GPU-Einstellungen
  * Benutzerbenachrichtigungen bei GPU-Fallbacks oder Konfigurationsproblemen

### Tests und Qualitätssicherung

Das Projekt enthält umfangreiche Tests zur Sicherstellung der Funktionalität und Performance:

#### Ausführen der Tests

```bash
# Alle Tests ausführen
./run_tests.sh

# Spezifische Tests ausführen
python -m pytest tests/test_hardware_detection.py
python -m pytest tests/test_status_banner.py
python -m pytest tests/test_integration.py
```

#### Performance-Tests

```bash
# Alle Performance-Tests ausführen
python tests/performance_test.py

# Nur Startup-Zeit messen
python tests/performance_test.py --startup

# Nur Persona-Switching-Zeit messen
python tests/performance_test.py --persona

# Nur Modell-Ladezeiten messen
python tests/performance_test.py --model

# Anzahl der Iterationen anpassen
python tests/performance_test.py --iterations 5
```

Die Ergebnisse der Performance-Tests werden im Verzeichnis `tests/results/` gespeichert.

#### Test-Typen

* **Unit-Tests**: Testen einzelne Komponenten isoliert
  * `test_hardware_detection.py`: Tests für die Hardware-Erkennung
  * `test_status_banner.py`: Tests für das Status-Banner

* **Integrationstests**: Testen das Zusammenspiel mehrerer Komponenten
  * `test_integration.py`: Tests für die Integration von Modell-Management, Hardware-Erkennung und Status-Banner

* **Performance-Tests**: Messen die Leistung verschiedener Funktionen
  * `performance_test.py`: Tests für Startup-Zeit, Persona-Switching und Modell-Ladezeiten

---

## ✅ Status

Der MVP ist stabil, startet zuverlässig und lässt sich um neue Personas, Modelle oder Features leicht erweitern.

Wenn du Lust hast, Abby sprechen zu lassen oder ein echtes Langzeitgedächtnis einzubauen – du weißt, wo du mich findest 😎

---

**Lizenz**: Noch nicht definiert. Frag den Boss 😉