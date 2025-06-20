import os
import sys
from contextlib import contextmanager

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QLabel, QHBoxLayout, QFrame, QInputDialog
)
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QMovie
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QEvent

from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
import re

# === Pfade & Einstellungen ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(r"C:\Users\bensc\Desktop\IT\KI_models", "em_german_mistral_v01.Q4_0.gguf")
GEDAECHTNIS_DATEI = os.path.join(BASE_DIR, "gedaechtnis.txt")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
SANDUHR_GIF = os.path.join(BASE_DIR, "sanduhr.gif")
CHUNKS_FILE = os.path.join(BASE_DIR, "chunks.pkl")
EMBEDDINGS_FILE = os.path.join(BASE_DIR, "embeddings.npy")
FAISS_INDEX_FILE = os.path.join(BASE_DIR, "index.faiss")

# Fehlerausgabe im Terminal unterdrücken
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

# Thread zur Ausführung des KI-Prompts (verhindert GUI-Einfrieren)
class QueryThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, llm, prompt):
        super().__init__()
        self.llm = llm
        self.prompt = prompt

    def run(self):
        try:
            response = self.llm(self.prompt, max_tokens=512, temperature=0.7)
            text = response["choices"][0]["text"].strip()
        except Exception as e:
            text = f"Fehler bei der Antwortgenerierung: {e}"
        self.finished.emit(text)

# Hauptklasse für das GUI-Programm
class ChatBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Projekt ChatBot")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(900, 600)
        self.move_to_center()

        # Layout erstellen
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Chat-Ausgabefeld
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 14))
        self.chat_display.setStyleSheet("background-color: black; color: white;")
        self.layout.addWidget(self.chat_display)

        # Status-Anzeige
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.status_label)

        # Eingabefeld
        self.input_field = QTextEdit()
        self.input_field.setFont(QFont("Arial", 14))
        self.input_field.setStyleSheet("background-color: white; color: black;")
        self.input_field.setFixedHeight(80)
        self.layout.addWidget(self.input_field)

        # Buttons unten
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.send_button = QPushButton("Senden (Enter)")
        self.send_button.setFont(QFont("Arial", 12))
        button_layout.addWidget(self.send_button)

        self.import_button = QPushButton("Dokument importieren")
        self.import_button.setFont(QFont("Arial", 12))
        button_layout.addWidget(self.import_button)

        # Aktionen verbinden
        self.send_button.clicked.connect(self.on_send_clicked)
        self.import_button.clicked.connect(self.on_import_clicked)
        self.input_field.installEventFilter(self)

        # Modelle vorbereiten
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.llm = None
        self.gedaechtnis_datei = GEDAECHTNIS_DATEI

        # Ladeanimation vorbereiten
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
        self.status_label.setText("Bereit für Fragen.")

    # Fenster zentrieren
    def move_to_center(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        center_point = screen_geometry.center()
        self.move(center_point - self.rect().center())

    # Platzhalter für Importfunktion
    def on_import_clicked(self):
        QMessageBox.information(self, "Import", "Dokument-Import-Funktion ist in Arbeit.")

    # Senden-Button-Klick
    def on_send_clicked(self):
        prompt = self.input_field.toPlainText().strip()
        if not prompt:
            return

        self.chat_display.append(f"<b>Du:</b> {prompt}")
        self.input_field.clear()

        if self.llm is None:
            self.status_label.setText("⏳ Lade Modell...")
            try:
                with suppress_stderr():
                    self.llm = Llama(
                        model_path=MODEL_PATH,
                        n_ctx=2048,
                        embedding=True,
                        n_threads=6,
                        system_prompt="Du bist ein hilfsbereiter, deutscher KI-Assistent. Antworte bitte immer auf Deutsch."
                    )
                self.status_label.setText("✅ Modell geladen")
            except Exception as e:
                self.status_label.setText(f"❌ Fehler beim Laden des Modells: {e}")
                return

        self.show_loading(True)
        self.thread = QueryThread(self.llm, prompt)
        self.thread.finished.connect(self.handle_response)
        self.thread.start()

    # Antwort anzeigen
    def handle_response(self, response):
        self.show_loading(False)
        self.chat_display.append(f"<b>Bot:</b> {response}")
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    # Eingabetaste abfangen
    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                else:
                    self.on_send_clicked()
                    return True
        return super().eventFilter(obj, event)

    # Wissensbasis vorbereiten (noch leer)
    def lade_wissensbasis(self):
        self.wissensbasis = {}

    def lade_index(self):
        return False

    # Lade-Animation zentrieren
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

# Hauptprogrammstart
if __name__ == "__main__":
    app = QApplication(sys.argv)
    chatbot = ChatBotApp()
    chatbot.show()
    sys.exit(app.exec())
