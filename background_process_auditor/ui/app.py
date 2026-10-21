"""
GUI Application for Background Process Auditor
Built with PySide6, Matplotlib, and custom auditor core components.
All UI text in Spanish.
"""

import sys
import time
from typing import List, Dict, Any

from PySide6.QtCore import QTimer, Qt, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from background_process_auditor.core.analyzer import AuditFinding, ProcessAnalyzer
from background_process_auditor.core.database import DatabaseManager
from background_process_auditor.core.exporter import CSVExporter
from background_process_auditor.core.monitor import ProcessMonitor, ProcessSample
from background_process_auditor.core.safety import SafetyGuard
from background_process_auditor.core.startup import StartupManager


class RealtimeChartCanvas(FigureCanvas):
    """Interactive Matplotlib Canvas for Real-time CPU & RAM trends."""

    def __init__(self, parent=None, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax_cpu = self.fig.add_subplot(211)
        self.ax_ram = self.fig.add_subplot(212)
        super().__init__(self.fig)
        self.setParent(parent)

        self.cpu_history: List[float] = []
        self.ram_history: List[float] = []
        self.time_history: List[float] = []

        self.fig.tight_layout(pad=2.0)

    def update_data(self, cpu_pct: float, ram_pct: float):
        self.cpu_history.append(cpu_pct)
        self.ram_history.append(ram_pct)
        self.time_history.append(len(self.time_history))

        if len(self.cpu_history) > 30:
            self.cpu_history.pop(0)
            self.ram_history.pop(0)
            self.time_history.pop(0)

        self.ax_cpu.cla()
        self.ax_ram.cla()

        self.ax_cpu.plot(self.cpu_history, color="#007ACC", linewidth=2, label="CPU (%)")
        self.ax_cpu.set_title("Uso Global de CPU (%)", fontsize=10, fontweight="bold")
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, linestyle="--", alpha=0.5)

        self.ax_ram.plot(self.ram_history, color="#28A745", linewidth=2, label="RAM (%)")
        self.ax_ram.set_title("Uso Global de RAM (%)", fontsize=10, fontweight="bold")
        self.ax_ram.set_ylim(0, 100)
        self.ax_ram.grid(True, linestyle="--", alpha=0.5)

        self.fig.tight_layout()
        self.draw()


class MainWindow(QMainWindow):
    """Main Application Window for Auditor de Procesos en Segundo Plano."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Auditor de Procesos en Segundo Plano - Windows 10 x64")
        self.resize(1100, 750)

        self.monitor = ProcessMonitor()
        self.analyzer = ProcessAnalyzer()
        self.startup_mgr = StartupManager()
        self.db_mgr = DatabaseManager()

        self.current_samples: List[ProcessSample] = []
        self.current_findings: List[AuditFinding] = []

        self._init_ui()

        # Update timer (2 seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_metrics)
        self.timer.start(2000)

        self.refresh_metrics()

    def _init_ui(self) -> None:
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Header Title Banner
        header = QLabel("Auditor de Procesos en Segundo Plano")
        header_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        header.setFont(header_font)
        header.setStyleSheet("color: #1A252C; margin-bottom: 5px;")
        main_layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tab_monitor = QWidget()
        self.tab_findings = QWidget()
        self.tab_startup = QWidget()
        self.tab_history = QWidget()

        self.tabs.addTab(self.tab_monitor, "Monitoreo en Tiempo Real")
        self.tabs.addTab(self.tab_findings, "Hallazgos y Diagnóstico")
        self.tabs.addTab(self.tab_startup, "Aplicaciones de Inicio")
        self.tabs.addTab(self.tab_history, "Histórico y Exportación")

        main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_widget)

        self._build_tab_monitor()
        self._build_tab_findings()
        self._build_tab_startup()
        self._build_tab_history()

    # --- TAB 1: MONITOREO REAL ---
    def _build_tab_monitor(self) -> None:
        layout = QHBoxLayout(self.tab_monitor)

        # Left panel: Charts
        left_box = QVBoxLayout()
        self.chart_canvas = RealtimeChartCanvas(self, width=4, height=4)
        left_box.addWidget(self.chart_canvas)

        self.lbl_system_summary = QLabel("Cargando métricas globales del sistema...")
        self.lbl_system_summary.setStyleSheet("background: #F0F4F8; padding: 10px; border-radius: 5px;")
        left_box.addWidget(self.lbl_system_summary)

        left_widget = QWidget()
        left_widget.setLayout(left_box)

        # Right panel: Process Table
        right_box = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Filtrar Proceso:"))
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Nombre o PID...")
        self.txt_filter.textChanged.connect(self.filter_process_table)
        search_layout.addWidget(self.txt_filter)
        right_box.addLayout(search_layout)

        self.tbl_processes = QTableWidget()
        self.tbl_processes.setColumnCount(7)
        self.tbl_processes.setHorizontalHeaderLabels([
            "PID", "Nombre de Proceso", "CPU (%)", "RAM (MB)", "Disco (KB/s)", "Evidencia Red", "Es Crítico"
        ])
        self.tbl_processes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_box.addWidget(self.tbl_processes)

        right_widget = QWidget()
        right_widget.setLayout(right_box)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 700])

        layout.addWidget(splitter)

    # --- TAB 2: HALLAZGOS Y DIAGNÓSTICO ---
    def _build_tab_findings(self) -> None:
        layout = QVBoxLayout(self.tab_findings)

        lbl_desc = QLabel(
            "Análisis continuo de procesos en segundo plano. Se identifican patrones de comportamiento "
            "clasificados estrictamente por nivel de Impacto y Confianza con evidencia verificada."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #4A5568; margin-bottom: 8px;")
        layout.addWidget(lbl_desc)

        self.tbl_findings = QTableWidget()
        self.tbl_findings.setColumnCount(8)
        self.tbl_findings.setHorizontalHeaderLabels([
            "PID", "Proceso", "Categoría", "Impacto", "Confianza", "Hora", "Duración", "Detalles y Evidencia"
        ])
        self.tbl_findings.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_findings)

    # --- TAB 3: APLICACIONES DE INICIO ---
    def _build_tab_startup(self) -> None:
        layout = QVBoxLayout(self.tab_startup)

        btn_bar = QHBoxLayout()
        self.btn_refresh_startup = QPushButton("Reesccanear Programas")
        self.btn_refresh_startup.clicked.connect(self.load_startup_items)
        btn_bar.addWidget(self.btn_refresh_startup)

        self.btn_restore_backup = QPushButton("Restaurar Configuración Anterior (Backup)")
        self.btn_restore_backup.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        self.btn_restore_backup.clicked.connect(self.restore_startup_backup)
        btn_bar.addWidget(self.btn_restore_backup)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        self.tbl_startup = QTableWidget()
        self.tbl_startup.setColumnCount(6)
        self.tbl_startup.setHorizontalHeaderLabels([
            "Nombre", "Comando / Ruta", "Ubicación", "Estado", "Tipo", "Acción"
        ])
        self.tbl_startup.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_startup)

        self.load_startup_items()

    # --- TAB 4: HISTÓRICO Y EXPORTACIÓN ---
    def _build_tab_history(self) -> None:
        layout = QVBoxLayout(self.tab_history)

        lbl_info = QLabel("Exportación e Histórico de Diagnósticos")
        lbl_info.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_info)

        btn_export = QPushButton("Exportar Hallazgos Diagnósticos a CSV")
        btn_export.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; padding: 10px;")
        btn_export.clicked.connect(self.export_findings_csv)
        layout.addWidget(btn_export)

        btn_export_proc = QPushButton("Exportar Procesos Actuales a CSV")
        btn_export_proc.setStyleSheet("background-color: #17A2B8; color: white; font-weight: bold; padding: 10px;")
        btn_export_proc.clicked.connect(self.export_processes_csv)
        layout.addWidget(btn_export_proc)

        layout.addStretch()

    # --- LOGIC & REFRESH METHODS ---
    @Slot()
    def refresh_metrics(self) -> None:
        # System totals
        totals = self.monitor.get_system_totals()
        self.chart_canvas.update_data(totals["cpu_percent"], totals["memory_percent"])

        net_mb = (totals["net_bytes_sent"] + totals["net_bytes_recv"]) / (1024 * 1024)
        summary_text = (
            f"<b>CPU Global:</b> {totals['cpu_percent']:.1f}% | "
            f"<b>RAM Usada:</b> {totals['memory_percent']:.1f}% | "
            f"<b>Tráfico Red Total:</b> {net_mb:.1f} MB"
        )
        self.lbl_system_summary.setText(summary_text)

        # Save snapshot to database
        now_str = time.strftime("%H:%M:%S")
        totals["timestamp_str"] = now_str
        self.db_mgr.save_system_snapshot(totals)

        # Sample process list
        self.current_samples = self.monitor.sample_processes()
        self.update_process_table(self.current_samples)

        # Analyze findings
        self.current_findings = self.analyzer.analyze_samples(self.current_samples)
        self.db_mgr.save_findings(self.current_findings)
        self.update_findings_table(self.current_findings)

    def update_process_table(self, samples: List[ProcessSample]) -> None:
        filter_text = self.txt_filter.text().strip().lower()
        filtered = [
            s for s in samples
            if filter_text in s.name.lower() or filter_text in str(s.pid)
        ] if filter_text else samples

        self.tbl_processes.setRowCount(len(filtered))
        for row, s in enumerate(filtered):
            self.tbl_processes.setItem(row, 0, QTableWidgetItem(str(s.pid)))
            self.tbl_processes.setItem(row, 1, QTableWidgetItem(s.name))
            self.tbl_processes.setItem(row, 2, QTableWidgetItem(f"{s.cpu_percent:.1f}%"))
            self.tbl_processes.setItem(row, 3, QTableWidgetItem(f"{s.memory_bytes / (1024*1024):.1f} MB"))
            disk_kb = (s.read_bytes + s.write_bytes) / 1024
            self.tbl_processes.setItem(row, 4, QTableWidgetItem(f"{disk_kb:.1f} KB"))

            net_ev = "Confirmada (Sockets)" if s.has_network_evidence else "Sin evidencia"
            item_net = QTableWidgetItem(net_ev)
            if s.has_network_evidence:
                item_net.setForeground(QColor("#007ACC"))
            self.tbl_processes.setItem(row, 5, item_net)

            item_crit = QTableWidgetItem("Sí" if s.is_critical else "No")
            if s.is_critical:
                item_crit.setForeground(QColor("#D9534F"))
            self.tbl_processes.setItem(row, 6, item_crit)

    @Slot()
    def filter_process_table(self) -> None:
        self.update_process_table(self.current_samples)

    def update_findings_table(self, findings: List[AuditFinding]) -> None:
        self.tbl_findings.setRowCount(len(findings))
        for row, f in enumerate(findings):
            self.tbl_findings.setItem(row, 0, QTableWidgetItem(str(f.pid)))
            self.tbl_findings.setItem(row, 1, QTableWidgetItem(f.process_name))
            self.tbl_findings.setItem(row, 2, QTableWidgetItem(f.category))

            item_imp = QTableWidgetItem(f.impact)
            if f.impact == "Alto":
                item_imp.setForeground(QColor("#D9534F"))
            elif f.impact == "Medio":
                item_imp.setForeground(QColor("#F0AD4E"))
            self.tbl_findings.setItem(row, 3, item_imp)

            item_conf = QTableWidgetItem(f.confidence)
            item_conf.setForeground(QColor("#28A745") if f.confidence == "Alta" else QColor("#6C757D"))
            self.tbl_findings.setItem(row, 4, item_conf)

            self.tbl_findings.setItem(row, 5, QTableWidgetItem(f.timestamp_str))
            self.tbl_findings.setItem(row, 6, QTableWidgetItem(f"{f.duration_seconds:.0f}s"))
            self.tbl_findings.setItem(row, 7, QTableWidgetItem(f.evidence_details))

    # --- STARTUP TAB ACTIONS ---
    def load_startup_items(self) -> None:
        items = self.startup_mgr.scan_startup_items()
        self.tbl_startup.setRowCount(len(items))

        for row, item in enumerate(items):
            self.tbl_startup.setItem(row, 0, QTableWidgetItem(item.name))
            self.tbl_startup.setItem(row, 1, QTableWidgetItem(item.command))
            self.tbl_startup.setItem(row, 2, QTableWidgetItem(item.location))

            status_str = "Habilitado" if item.enabled else "Deshabilitado"
            self.tbl_startup.setItem(row, 3, QTableWidgetItem(status_str))

            type_str = "Esencial / Sistema" if item.is_essential else "No Esencial / Terceros"
            item_type = QTableWidgetItem(type_str)
            if item.is_essential:
                item_type.setForeground(QColor("#D9534F"))
            self.tbl_startup.setItem(row, 4, item_type)

            btn = QPushButton("Deshabilitar" if item.enabled else "Habilitar")
            btn.setEnabled(not item.is_essential)
            btn.clicked.connect(lambda checked=False, item_id=item.id, target_enable=not item.enabled: self.toggle_startup_item(item_id, target_enable))
            self.tbl_startup.setCellWidget(row, 5, btn)

    def toggle_startup_item(self, item_id: str, enable: bool) -> None:
        action_word = "habilitar" if enable else "deshabilitar"
        reply = QMessageBox.question(
            self,
            "Confirmación Requerida",
            f"¿Está seguro de que desea {action_word} este programa de inicio?\n\n"
            "Se guardará automáticamente una copia de respaldo de la configuración anterior.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.startup_mgr.toggle_item(item_id, enable)
            if success:
                QMessageBox.information(self, "Operación Exitosa", msg)
            else:
                QMessageBox.warning(self, "Acción Bloqueada", msg)
            self.load_startup_items()

    def restore_startup_backup(self) -> None:
        backups = self.startup_mgr.list_backups()
        if not backups:
            QMessageBox.information(self, "Sin Respaldos", "No existen respaldos previos registrados.")
            return

        reply = QMessageBox.question(
            self,
            "Restaurar Respaldo",
            "¿Desea restaurar la configuración anterior de aplicaciones de inicio desde la copia de respaldo más reciente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            ok = self.startup_mgr.restore_backup()
            if ok:
                QMessageBox.information(self, "Restauración Completada", "La configuración de inicio anterior se ha restaurado con éxito.")
                self.load_startup_items()
            else:
                QMessageBox.critical(self, "Error", "No se pudo cargar el archivo de respaldo.")

    # --- EXPORT ACTIONS ---
    def export_findings_csv(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Informe de Hallazgos", "hallazgos_proceso_background.csv", "Archivos CSV (*.csv)"
        )
        if filepath:
            CSVExporter.export_findings_to_csv(self.current_findings, filepath)
            QMessageBox.information(self, "Exportación Exitosa", f"Informe guardado correctamente en:\n{filepath}")

    def export_processes_csv(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Muestreo de Procesos", "procesos_activos.csv", "Archivos CSV (*.csv)"
        )
        if filepath:
            CSVExporter.export_process_samples_to_csv(self.current_samples, filepath)
            QMessageBox.information(self, "Exportación Exitosa", f"Informe de procesos guardado correctamente en:\n{filepath}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
