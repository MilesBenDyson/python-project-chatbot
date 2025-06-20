# 🤖 Python Projekt: Lokaler Dokumenten-ChatBot

Ein vollständig **offline-fähiger KI-ChatBot mit grafischer Oberfläche (PyQt6)**, der eigene Dokumente (`.txt`, `.pdf`, `.docx`) importieren, analysieren und dauerhaft in einer **thematisch geordneten Wissensbasis** speichert.  
Fragen an diese Dokumente werden mithilfe eines lokal laufenden **llama-cpp-python**-Modells (z. B. `em_german_mistral_v01.Q4_0.gguf`) beantwortet – ganz ohne Internetverbindung.

---

## 🚀 Features

- Lokale GUI mit **PyQt6**
- Offline-KI via **llama-cpp-python**
- Unterstützung für `.txt`, `.pdf`, `.docx`
- **Thematisch strukturierte Wissensablage** (`wissen/<thema>/`)
- **Semantische Vektorsuche** mit FAISS & SentenceTransformers
- Fortschrittsanzeige & Ladeanimation (GIF)
- Antwortfenster mit Chatverlauf
- Optionale Gedächtnisfunktion (Dateispeicherung)

---

## 🛠 Installation

### 1. Projekt klonen

```bash
git clone https://github.com/MilesBenDyson/python-project-chatbot.git
cd python-project-chatbot
```

### 2. Virtuelle Umgebung erstellen

```bash
python -m venv .venv
source .venv/Scripts/activate  # Git Bash / Linux / macOS
# oder
.venv\Scripts\activate         # Windows CMD / PowerShell
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

---

## 🧠 Nutzung

```bash
python ChatBotNeu.py
```

1. Dokument über die GUI importieren
2. Thema benennen (z. B. "Sozialrecht", "Medizin")
3. Fragen stellen – Antworten kommen direkt im Chatfenster
4. Wissen wird thematisch im `wissen/`-Verzeichnis gespeichert

---

## ⚙️ Voraussetzungen

- Python **3.10 – 3.12** empfohlen
- Eine GGUF-Modell-Datei wie:

```plaintext
em_german_mistral_v01.Q4_0.gguf
```

- Modell liegt im Pfad:

```plaintext
C:\Users\bensc\Desktop\IT\KI_models\
```

⚠️ **Hinweis:** Achte auf ausreichend Arbeitsspeicher (ggf. RAM-optimiertes Modell verwenden)

---

## 📂 Projektstruktur

```plaintext
python-project-chatbot/
│
├── ChatBotNeu.py            # Haupt-GUI mit KI-Anbindung
├── requirements.txt         # Abhängigkeiten
├── .gitignore               # Git-Ausnahmen
├── icon.ico                 # Fenster-Icon
├── sanduhr.gif              # Ladeanimation
└── wissen/                  # Themenbasierte Dokumentenspeicherung
```

---

## 🧪 Beispiel

> Thema: **"Pflegegrad 3"**  
> Frage: _„Welche Voraussetzungen gelten für den Pflegegrad 3 bei Kindern mit Downsyndrom?“_  
> → Der ChatBot durchsucht die entsprechenden Dokumente im Hintergrund und liefert relevante Informationen.

---

## 🔐 Privatsphäre

Alle Datenverarbeitung findet **lokal** auf deinem Gerät statt.  
Es werden **keine Daten an externe Server gesendet oder gespeichert**.

---

## 🤘 Autor

Ben alias **MilesBenDyson**  
Metalhead • Bastler • Sozialarbeiter • Vater • KI-Rebell

---

## 📜 Lizenz

MIT License – nutze es, verbessere es, teile es.
