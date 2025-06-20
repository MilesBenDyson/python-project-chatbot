
# 🧠 Python Projekt: Lokaler Dokumenten-ChatBot

Ein vollständig offline-fähiger KI-ChatBot mit grafischer Oberfläche (PyQt6), der eigene Dokumente (.txt, .pdf, .docx) importieren, analysieren und dauerhaft in einer Wissensbasis speichern kann. Fragen an diese Dokumente werden mithilfe eines lokalen GPT4All-Modells (Mistral) beantwortet – ganz ohne Internetverbindung.

---

## 🚀 Features

- Lokale GUI mit PyQt6
- Offline-KI über [GPT4All](https://gpt4all.io) mit Mistral-Modell
- Dokumentenimport aus `.txt`, `.pdf` und `.docx`
- Themenbasierte Wissensablage (`wissen/<thema>/`)
- Semantische Suche mit FAISS und SentenceTransformers
- Ladeanimation mit GIF
- Speichereingabe (Gedächtnisfunktion)

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

## 💡 Nutzung

```bash
python ChatBotNeu.py
```

1. Dokument importieren (Button klicken)
2. Thema benennen (z. B. "Gesundheit")
3. Fragen zu deinem Thema stellen
4. Chatverlauf und Antworten erscheinen direkt im Fenster

---

## ⚙️ Voraussetzungen

- Python 3.10–3.12 empfohlen
- Lokale GGUF-Modell-Datei (z. B. `em_german_mistral_v01.Q4_K_M.gguf`) im Pfad:

```plaintext
C:\Users\bensc\Desktop\IT\KI_models
```

---

## 📂 Projektstruktur

```plaintext
python-project-chatbot/
│
├── ChatBotNeu.py           # Hauptdatei mit PyQt-GUI
├── requirements.txt        # Benötigte Python-Pakete
├── .gitignore              # Ausschlüsse für Git
├── icon.ico                # Fenster-Icon
├── sanduhr.gif             # Ladeanimation
└── wissen/                 # Thematisch gespeicherte Dokumente
```

---

## 🧠 Beispiel

> Thema: **"Gesundheit"**  
> Frage: _„Was ist der Unterschied zwischen Grippe und Erkältung?“_  
> → Der Bot liefert passende Informationen aus dem importierten Text.

---

## 🛡 Hinweis zur Privatsphäre

Alle Datenverarbeitung findet **lokal** auf deinem Gerät statt. Es werden **keine Informationen an externe Server gesendet**.

---

## 🤘 Autor

Ben alias **MilesBenDyson**  
Metalhead • Bastler • Sozialarbeiter • Vater • KI-Rebell

---

## 📜 Lizenz

MIT License – nutze es, verbessere es, teile es.
