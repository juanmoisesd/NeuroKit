from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QLabel, QComboBox, QSlider, QListWidget,
    QDockWidget, QToolBar, QMessageBox, QStyle
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QTextCursor, QTextCharFormat, QColor

class MainWindow(QMainWindow):
    # Signals to communicate with the main controller
    open_file_signal = Signal(str)
    play_signal = Signal()
    pause_signal = Signal()
    stop_signal = Signal()
    next_signal = Signal()
    prev_signal = Signal()
    voice_changed_signal = Signal(str)
    rate_changed_signal = Signal(int)
    page_changed_signal = Signal(int)
    recent_file_clicked_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Voice Reader Español")
        self.setMinimumSize(800, 600)

        self.setAcceptDrops(True)

        self._setup_ui()
        self._setup_actions()

    def _setup_ui(self):
        # Central widget: Text viewer
        self.text_viewer = QTextEdit()
        self.text_viewer.setReadOnly(True)
        self.setCentralWidget(self.text_viewer)

        # Toolbar
        self.toolbar = QToolBar("Controles de Reproducción")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Dock: Library and Settings
        self.dock = QDockWidget("Panel de Control", self)
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        dock_widget = QWidget()
        dock_layout = QVBoxLayout(dock_widget)

        # Settings: Voice
        dock_layout.addWidget(QLabel("Voz:"))
        self.voice_combo = QComboBox()
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        dock_layout.addWidget(self.voice_combo)

        # Settings: Speed
        dock_layout.addWidget(QLabel("Velocidad de Lectura:"))
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(50, 300)
        self.rate_slider.setValue(150)
        self.rate_slider.valueChanged.connect(self._on_rate_changed)
        dock_layout.addWidget(self.rate_slider)

        # Navigation: Page
        nav_layout = QHBoxLayout()
        self.page_label = QLabel("Página: 0 / 0")
        nav_layout.addWidget(self.page_label)

        self.prev_page_btn = QPushButton("Pág Ant")
        self.prev_page_btn.clicked.connect(lambda: self._change_page(-1))
        nav_layout.addWidget(self.prev_page_btn)

        self.next_page_btn = QPushButton("Pág Sig")
        self.next_page_btn.clicked.connect(lambda: self._change_page(1))
        nav_layout.addWidget(self.next_page_btn)
        dock_layout.addLayout(nav_layout)

        # Library
        dock_layout.addWidget(QLabel("Documentos Recientes:"))
        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self._on_recent_clicked)
        dock_layout.addWidget(self.recent_list)

        self.dock.setWidget(dock_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

    def _setup_actions(self):
        style = self.style()

        # Open
        open_icon = style.standardIcon(QStyle.SP_DialogOpenButton)
        open_action = QAction(open_icon, "Abrir PDF", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file_dialog)
        self.toolbar.addAction(open_action)
        self.toolbar.addSeparator()

        # Play
        play_icon = style.standardIcon(QStyle.SP_MediaPlay)
        self.play_action = QAction(play_icon, "Reproducir", self)
        self.play_action.setShortcut("Space")
        self.play_action.triggered.connect(self.play_signal.emit)
        self.toolbar.addAction(self.play_action)

        # Pause
        pause_icon = style.standardIcon(QStyle.SP_MediaPause)
        self.pause_action = QAction(pause_icon, "Pausar", self)
        self.pause_action.triggered.connect(self.pause_signal.emit)
        self.toolbar.addAction(self.pause_action)

        # Stop
        stop_icon = style.standardIcon(QStyle.SP_MediaStop)
        self.stop_action = QAction(stop_icon, "Detener", self)
        self.stop_action.triggered.connect(self.stop_signal.emit)
        self.toolbar.addAction(self.stop_action)

        self.toolbar.addSeparator()

        # Prev Paragraph
        prev_icon = style.standardIcon(QStyle.SP_MediaSkipBackward)
        prev_action = QAction(prev_icon, "Párrafo Anterior", self)
        prev_action.setShortcut("Left")
        prev_action.triggered.connect(self.prev_signal.emit)
        self.toolbar.addAction(prev_action)

        # Next Paragraph
        next_icon = style.standardIcon(QStyle.SP_MediaSkipForward)
        next_action = QAction(next_icon, "Párrafo Siguiente", self)
        next_action.setShortcut("Right")
        next_action.triggered.connect(self.next_signal.emit)
        self.toolbar.addAction(next_action)

        self._update_play_state(False, False)

    def open_file_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "Archivos PDF (*.pdf)")
        if filename:
            self.open_file_signal.emit(filename)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.open_file_signal.emit(file_path)
                break # Only handle the first PDF

    def set_voices(self, voices, selected_id):
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        for idx, (vid, name) in enumerate(voices):
            self.voice_combo.addItem(name, vid)
            if vid == selected_id:
                self.voice_combo.setCurrentIndex(idx)
        self.voice_combo.blockSignals(False)

    def set_rate(self, rate):
        self.rate_slider.blockSignals(True)
        self.rate_slider.setValue(rate)
        self.rate_slider.blockSignals(False)

    def update_recent_files(self, files):
        self.recent_list.clear()
        for f in files:
            self.recent_list.addItem(f)

    def _on_voice_changed(self, index):
        voice_id = self.voice_combo.itemData(index)
        if voice_id:
            self.voice_changed_signal.emit(voice_id)

    def _on_rate_changed(self, value):
        self.rate_changed_signal.emit(value)

    def _on_recent_clicked(self, item):
        self.recent_file_clicked_signal.emit(item.text())

    def _change_page(self, delta):
        # We need the current page and max pages from the controller,
        # so we just emit a signal for next/prev page.
        # However, to keep it simple, we can emit a delta signal or let controller handle it.
        # Let's add a property to track current page locally for UI buttons, but controller manages truth.
        pass # implemented via page_changed_signal or similar if needed.
        # Actually, let's just emit standard next/prev page signals.

    def display_text(self, blocks):
        """Displays text blocks in the viewer."""
        self.text_viewer.clear()
        for i, block in enumerate(blocks):
            # Append text. We can store the block index in user data if needed.
            self.text_viewer.append(block['text'] + "\n")

        # Scroll to top
        cursor = self.text_viewer.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.text_viewer.setTextCursor(cursor)

    def highlight_paragraph(self, block_index, blocks):
        """Highlights the currently reading paragraph without re-rendering."""
        if not blocks or block_index < 0 or block_index >= len(blocks):
            return

        cursor = self.text_viewer.textCursor()

        # Clear all formatting first
        cursor.select(QTextCursor.Document)
        format_normal = QTextCharFormat()
        cursor.setCharFormat(format_normal)

        # Now find the specific block and highlight it
        # We rely on the QTextDocument blocks which map to our paragraphs
        document = self.text_viewer.document()
        doc_block = document.findBlockByNumber(block_index)

        if doc_block.isValid():
            cursor.setPosition(doc_block.position())
            cursor.setPosition(doc_block.position() + doc_block.length() - 1, QTextCursor.KeepAnchor)

            format_highlight = QTextCharFormat()
            format_highlight.setBackground(QColor("yellow"))
            format_highlight.setForeground(QColor("black"))
            cursor.setCharFormat(format_highlight)

            # Scroll to the highlighted paragraph
            self.text_viewer.setTextCursor(cursor)

    def set_page_info(self, current, total):
        self.page_label.setText(f"Página: {current} / {total}")

    def _update_play_state(self, playing, paused):
        self.play_action.setEnabled(not playing or paused)
        self.pause_action.setEnabled(playing and not paused)
        self.stop_action.setEnabled(playing or paused)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
