import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from ui import MainWindow
from config import ConfigManager
from tts_engine import TTSEngine
from pdf_extractor import PDFExtractor

class MainController(QObject):
    update_ui_signal = Signal(dict)
    tts_finished_signal = Signal(bool)

    def __init__(self, view: MainWindow):
        super().__init__()
        self.view = view
        self.config = ConfigManager()
        self.tts = TTSEngine()
        self.pdf = PDFExtractor()

        self.current_page = 0
        self.current_block_index = 0
        self.blocks = []

        self._setup_connections()
        self._init_ui_state()

    def _setup_connections(self):
        # View to Controller
        self.view.open_file_signal.connect(self.load_pdf)
        self.view.play_signal.connect(self.play)
        self.view.pause_signal.connect(self.pause)
        self.view.stop_signal.connect(self.stop)
        self.view.next_signal.connect(self.next_block)
        self.view.prev_signal.connect(self.prev_block)
        self.view.voice_changed_signal.connect(self.change_voice)
        self.view.rate_changed_signal.connect(self.change_rate)
        self.view.recent_file_clicked_signal.connect(self.load_pdf)

        # Override UI page buttons to use controller logic
        self.view.next_page_btn.clicked.disconnect()
        self.view.next_page_btn.clicked.connect(self.next_page)
        self.view.prev_page_btn.clicked.disconnect()
        self.view.prev_page_btn.clicked.connect(self.prev_page)

        # Controller signals to View (thread-safe UI updates)
        # Using a dictionary to pass different types of updates if needed
        # but for simplicity, we can just call view methods directly
        # since TTS callbacks are executed in a separate thread.
        # It's better to use Signals to update UI from TTS thread.

        # Internal signal routing to handle TTS thread callbacks
        self.tts_finished_signal.connect(self._handle_tts_finish)

        # TTS to Controller
        self.tts.set_callbacks(on_finish=self._on_tts_finish)

    def _init_ui_state(self):
        # Load voices
        voices = self.tts.get_available_voices()
        saved_voice = self.config.get("voice_id")
        # If no saved voice, try to get the default one
        if not saved_voice:
            saved_voice = self.tts.get_default_voice()
        self.view.set_voices(voices, saved_voice)

        # Load rate
        rate = self.config.get("rate", 150)
        self.tts.set_rate(rate)
        self.view.set_rate(rate)

        # Load recent files
        self.view.update_recent_files(self.config.get_recent_files())

    @Slot(str)
    def load_pdf(self, filepath):
        if not os.path.exists(filepath):
            self.view.show_error(f"No se pudo encontrar el archivo: {filepath}")
            return

        try:
            self.stop()
            self.pdf.load_document(filepath)
            self.config.add_recent_file(filepath)
            self.view.update_recent_files(self.config.get_recent_files())

            # Restore position
            page, block = self.config.get_last_position(filepath)
            self.current_page = max(0, min(page, self.pdf.num_pages - 1))
            self.current_block_index = block

            self._load_current_page()

        except Exception as e:
            self.view.show_error(f"Error al abrir el PDF: {e}")

    def _load_current_page(self):
        if not self.pdf.doc:
            return

        self.view.set_page_info(self.current_page + 1, self.pdf.num_pages)
        self.blocks = self.pdf.extract_page(self.current_page, ocr_lang=self.config.get("ocr_language", "spa"))

        if self.current_block_index >= len(self.blocks):
            self.current_block_index = 0

        self.view.display_text(self.blocks)
        if self.blocks:
            self.view.highlight_paragraph(self.current_block_index, self.blocks)

        self.config.save_last_position(self.pdf.filepath, self.current_page, self.current_block_index)

    @Slot()
    def play(self):
        if not self.pdf.doc or not self.blocks:
            return

        if self.tts.is_paused:
            self.tts.resume()
            self.view._update_play_state(True, False)
            return

        if self.current_block_index < len(self.blocks):
            text = self.blocks[self.current_block_index]['text']
            self.view.highlight_paragraph(self.current_block_index, self.blocks)
            self.view._update_play_state(True, False)
            self.tts.speak(text)
        else:
            self.next_page()
            if self.current_page < self.pdf.num_pages:
                self.play()

    @Slot()
    def pause(self):
        if self.tts.is_playing:
            self.tts.pause()
            self.view._update_play_state(True, True)

    @Slot()
    def stop(self):
        self.tts.stop()
        self.view._update_play_state(False, False)

    @Slot()
    def next_block(self):
        self.stop()
        self.current_block_index += 1
        if self.current_block_index >= len(self.blocks):
            self.next_page()
        else:
            self.view.highlight_paragraph(self.current_block_index, self.blocks)
            self.config.save_last_position(self.pdf.filepath, self.current_page, self.current_block_index)

    @Slot()
    def prev_block(self):
        self.stop()
        self.current_block_index -= 1
        if self.current_block_index < 0:
            if self.current_page > 0:
                self.prev_page()
                self.current_block_index = len(self.blocks) - 1 if self.blocks else 0
                self.view.highlight_paragraph(self.current_block_index, self.blocks)
                self.config.save_last_position(self.pdf.filepath, self.current_page, self.current_block_index)
        else:
            self.view.highlight_paragraph(self.current_block_index, self.blocks)
            self.config.save_last_position(self.pdf.filepath, self.current_page, self.current_block_index)

    @Slot()
    def next_page(self):
        self.stop()
        if self.current_page < self.pdf.num_pages - 1:
            self.current_page += 1
            self.current_block_index = 0
            self._load_current_page()

    @Slot()
    def prev_page(self):
        self.stop()
        if self.current_page > 0:
            self.current_page -= 1
            self.current_block_index = 0
            self._load_current_page()

    @Slot(str)
    def change_voice(self, voice_id):
        self.tts.set_voice(voice_id)
        self.config.set("voice_id", voice_id)

    @Slot(int)
    def change_rate(self, rate):
        self.tts.set_rate(rate)
        self.config.set("rate", rate)

    def _on_tts_finish(self, completed):
        # This is called from the TTS thread.
        # We must use a Signal to safely jump back to the GUI thread.
        self.tts_finished_signal.emit(completed)

    @Slot(bool)
    def _handle_tts_finish(self, completed):
        # This executes in the main GUI thread
        if completed and not self.tts.is_paused:
            self._auto_next_block()

    def _auto_next_block(self):
        # Continue to next block automatically if playing
        self.current_block_index += 1
        if self.current_block_index < len(self.blocks):
            self.config.save_last_position(self.pdf.filepath, self.current_page, self.current_block_index)
            self.play()
        else:
            if self.current_page < self.pdf.num_pages - 1:
                self.next_page()
                self.play()
            else:
                self.stop()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Voice Reader")

    view = MainWindow()
    controller = MainController(view)

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
