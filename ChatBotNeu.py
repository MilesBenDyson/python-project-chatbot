import os
import sys
from contextlib import contextmanager

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QLabel, QHBoxLayout, QFrame, QInputDialog
)
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QKeyEvent, QMovie
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from gpt4all import GPT4All
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
import re

# === Pfade & Einstellungen ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = r"C:\Users\bensc\Desktop\IT\KI_models"
MODEL_NAME = "em_german_mistral_v01.Q4_K_M.gguf"
MODEL_TYPE = "llama"
GEDAECHTNIS_DATEI = os.path.join(BASE_DIR, "gedaechtnis.txt")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
SANDUHR_GIF = os.path.join(BASE_DIR, "sanduhr.gif")  # Falls vorhanden
CHUNKS_FILE = os.path.join(BASE_DIR, "chunks.pkl")
EMBEDDINGS_FILE = os.path.join(BASE_DIR, "embeddings.npy")
FAISS_INDEX_FILE = os.path.join(BASE_DIR, "index.faiss")


@contextmanager
def suppress_stderr():
    stderr_fileno = sys.stderr.fileno()
    with open(os.devnull, "w") as devnull:
        old_stderr = os.dup(stderr_fileno)
        os.dup2(devnull.fileno(), stderr_fileno)
        try:
            yield
        finally:
            os.dup2(old_stderr, stderr_fileno)


class QueryThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, llm, query):
        super().__init__()
        self.llm = llm
        self.query = query

    def run(self):
        try:
            response = self.llm.generate(prompt=self.query, temp=0.7, n_predict=512)
        except Exception as e:
            response = f"Fehler bei der Antwortgenerierung: {e}"
        self.finished.emit(response)


class ChatBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Projekt ChatBot")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(900, 600)
        self.center()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 14))
        self.chat_display.setStyleSheet("background-color: black; color: white;")
        self.layout.addWidget(self.chat_display)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.status_label)

        self.input_field = QTextEdit()
        self.input_field.setFont(QFont("Arial", 14))
        self.input_field.setStyleSheet("background-color: white; color: black;")
        self.input_field.setFixedHeight(80)
        self.layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.send_button = QPushButton("Senden (Enter)")
        self.send_button.setFont(QFont("Arial", 12))
        button_layout.addWidget(self.send_button)

        self.import_button = QPushButton("Dokument importieren")
        self.import_button.setFont(QFont("Arial", 12))
        button_layout.addWidget(self.import_button)

        self.send_button.clicked.connect(self.on_send_clicked)
        self.import_button.clicked.connect(self.on_import_clicked)
        self.input_field.installEventFilter(self)

        self.documents = []
        self.document_embeddings = []
        self.index = None
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.llm = None

        self.gedaechtnis_datei = GEDAECHTNIS_DATEI

        self.loading_label = QFrame(self)
        self.loading_label.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.loading_label.setVisible(False)
        self.loading_label.setGeometry(0, 0, self.width(), self.height())

        self.gif_label = QLabel(self.loading_label)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if os.path.exists(SANDUHR_GIF):
            self.loading_movie = QMovie(SANDUHR_GIF)
            self.gif_label.setMovie(self.loading_movie)
            size = self.loading_movie.currentPixmap().size()
            if size.isEmpty():
                self.loading_movie.start()
                self.loading_movie.stop()
                size = self.loading_movie.currentPixmap().size()
            self.gif_label.setFixedSize(size)
        else:
            self.loading_movie = None

        self.resizeEvent = self.on_resize
        self.position_loading_gif()

        self.lade_wissensbasis()
        if self.lade_index():
            if self.wissensbasis:
                self.chat_display.append("<b>Bot:</b> Wissen wurde geladen. Stelle mir Fragen dazu!")
            else:
                self.chat_display.append("<b>Bot:</b> Hallo! Importiere ein Dokument und stelle mir Fragen dazu!")
        else:
            self.chat_display.append("<b>Bot:</b> Hallo! Importiere ein Dokument und stelle mir Fragen dazu!")

        self.status_label.setText("LLM wird geladen...")
        QTimer.singleShot(100, self.load_llm)

    def on_import_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Dokument auswählen", "", "Textdateien (*.txt);;PDF-Dateien (*.pdf);;Word-Dokumente (*.docx)")
        if not path:
            return

        thema, ok = QInputDialog.getText(self, "Thema eingeben", "Wie soll dieses Thema heißen?")
        if not ok or not thema.strip():
            QMessageBox.warning(self, "Abbruch", "Kein Thema angegeben.")
            return

        thema = thema.strip().lower().replace(" ", "_")
        wissen_pfad = os.path.join(BASE_DIR, "wissen", thema)
        os.makedirs(wissen_pfad, exist_ok=True)

        ext = os.path.splitext(path)[1].lower()
        text = ""
        try:
            if ext == ".txt":
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            elif ext == ".pdf":
                import fitz
                doc = fitz.open(path)
                text = "\n".join(page.get_text() for page in doc)
            elif ext == ".docx":
                from docx import Document
                doc = Document(path)
                text = "\n".join(p.text for p in doc.paragraphs)
            else:
                QMessageBox.warning(self, "Fehler", f"Dateityp {ext} wird nicht unterstützt.")
                return
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden:\n{e}")
            return

        if not text.strip():
            QMessageBox.warning(self, "Fehler", "Dokument ist leer.")
            return

        with open(os.path.join(wissen_pfad, "text.txt"), "w", encoding="utf-8") as f:
            f.write(text)

        CHUNK_SIZE = 500
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current = ""
        for s in sentences:
            if len(current) + len(s) < CHUNK_SIZE:
                current += s + " "
            else:
                chunks.append(current.strip())
                current = s + " "
        if current:
            chunks.append(current.strip())

        embeddings = self.embedding_model.encode(chunks)
        index = faiss.IndexFlatL2(384)
        index.add(embeddings)

        np.save(os.path.join(wissen_pfad, "embeddings.npy"), embeddings)
        faiss.write_index(index, os.path.join(wissen_pfad, "index.faiss"))

        QMessageBox.information(self, "Fertig", f"Thema '{thema}' wurde importiert und gespeichert.")
        self.lade_wissensbasis()

    def finde_relevante_texte(self, query, top_k=2):
        relevante_chunks = []
        query_vec = self.embedding_model.encode([query])[0]

        for thema, daten in self.wissensbasis.items():
            try:
                D, I = daten["index"].search(query_vec.reshape(1, -1), top_k)
                for i in I[0]:
                    relevante_chunks.append(daten["chunks"][i])
            except Exception as e:
                print(f"Fehler bei Suche in Thema '{thema}': {e}")
                continue

        return relevante_chunks

    def lade_wissensbasis(self):
        self.wissensbasis = {}
        wissen_dir = os.path.join(BASE_DIR, "wissen")
        if not os.path.exists(wissen_dir):
            return

        for thema in os.listdir(wissen_dir):
            pfad = os.path.join(wissen_dir, thema)
            if not os.path.isdir(pfad):
                continue

            try:
                txt_path = os.path.join(pfad, "text.txt")
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()

                CHUNK_SIZE = 500
                sentences = re.split(r'(?<=[.!?]) +', text)
                chunks = []
                current = ""
                for s in sentences:
                    if len(current) + len(s) < CHUNK_SIZE:
                        current += s + " "
                    else:
                        chunks.append(current.strip())
                        current = s + " "
                if current:
                    chunks.append(current.strip())

                embeddings = np.load(os.path.join(pfad, "embeddings.npy"))
                index = faiss.read_index(os.path.join(pfad, "index.faiss"))

                self.wissensbasis[thema] = {
                    "chunks": chunks,
                    "index": index
                }
            except Exception as e:
                print(f"Fehler beim Laden von Thema '{thema}': {e}")

    def lade_index(self):
        if os.path.exists(CHUNKS_FILE) and os.path.exists(EMBEDDINGS_FILE) and os.path.exists(FAISS_INDEX_FILE):
            with open(CHUNKS_FILE, "rb") as f:
                self.documents = pickle.load(f)
            self.document_embeddings = np.load(EMBEDDINGS_FILE)
            self.index = faiss.read_index(FAISS_INDEX_FILE)
            return True
        return False

    def on_send_clicked(self):
        if not self.llm:
            QMessageBox.warning(self, "Fehler", "Das Modell wurde nicht geladen.")
            return

        query = self.input_field.toPlainText().strip()
        if not query:
            return

        self.chat_display.append(f"<b>Du:</b> {query}")
        self.input_field.clear()

        gedaechtnis_text = self.lade_gedaechtnis()
        relevante_chunks = self.finde_relevante_texte(query)
        kontext = "\n".join(relevante_chunks)

        prompt = f"""[System]
Du bist ein hilfreicher Assistent. Antworte präzise und hilfreich.

[Gedächtnis]
{gedaechtnis_text}

[Dokumenten-Kontext]
{kontext}

[Frage]
{query}

[Antwort]"""

        self.show_loading(True)

        self.thread = QueryThread(self.llm, prompt)
        self.thread.finished.connect(self.handle_response)
        self.thread.start()

    def handle_response(self, response):
        self.show_loading(False)
        self.chat_display.append(f"<b>Bot:</b> {response}")
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_resize(self, event):
        self.position_loading_gif()
        event.accept()

    def show_loading(self, show=True):
        self.loading_label.setVisible(show)
        if self.loading_movie:
            if show:
                self.loading_movie.start()
            else:
                self.loading_movie.stop()

    def position_loading_gif(self):
        self.loading_label.setGeometry(0, 0, self.width(), self.height())
        if self.gif_label:
            self.gif_label.move(
                (self.width() - self.gif_label.width()) // 2,
                (self.height() - self.gif_label.height()) // 2,
            )

    def load_llm(self):
        try:
            with suppress_stderr():
                self.llm = GPT4All(
                    model_name=MODEL_NAME,
                    model_path=MODEL_PATH,
                    model_type=MODEL_TYPE,
                    allow_download=False
                )
            self.status_label.setText("Modell erfolgreich geladen!")
        except Exception as e:
            self.status_label.setText(f"Fehler beim Laden des Modells: {e}")

    def lade_gedaechtnis(self):
        if os.path.exists(self.gedaechtnis_datei):
            with open(self.gedaechtnis_datei, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    chatbot = ChatBotApp()
    chatbot.show()
    sys.exit(app.exec())
