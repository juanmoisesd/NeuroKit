import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QComboBox, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon

from src.network.adapter import NetworkAdapter
from src.network.connectivity import ConnectivityChecker
from src.wifi.scanner import WiFiScanner
from src.optimizer.config_manager import ConfigManager, OptimizerMode
from src.monitoring.engine import MonitoringEngine
from src.storage.db import DatabaseManager
from src.reports.exporter import ReportExporter

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WiFi Performance Manager")
        self.setMinimumSize(800, 600)

        # Initialize core components
        self.db = DatabaseManager()
        self.adapter = NetworkAdapter()
        self.checker = ConnectivityChecker()
        self.scanner = WiFiScanner()
        self.optimizer = ConfigManager(self.db)
        self.monitor = MonitoringEngine(self.db)
        self.exporter = ReportExporter(self.db)

        # Setup UI
        self._setup_ui()

        # Setup Timers for UI updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(5000) # Update every 5 seconds

        # Initial population
        self._update_status()
        self.monitor.start()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Status
        self.status_tab = QWidget()
        self._setup_status_tab()
        self.tabs.addTab(self.status_tab, "Estado y Calidad")

        # Tab 2: Scanner
        self.scanner_tab = QWidget()
        self._setup_scanner_tab()
        self.tabs.addTab(self.scanner_tab, "Analizador Wi-Fi")

        # Tab 3: Optimizer
        self.optimizer_tab = QWidget()
        self._setup_optimizer_tab()
        self.tabs.addTab(self.optimizer_tab, "Optimizador")

        # Tab 4: Reports
        self.reports_tab = QWidget()
        self._setup_reports_tab()
        self.tabs.addTab(self.reports_tab, "Informes y Ajustes")

    def _setup_status_tab(self):
        layout = QVBoxLayout(self.status_tab)

        # Connection Status Group
        status_group = QGroupBox("Estado de la Conexión")
        status_layout = QVBoxLayout(status_group)

        self.lbl_adapter = QLabel("Adaptador: Calculando...")
        self.lbl_ssid = QLabel("SSID: Calculando...")
        self.lbl_signal = QLabel("Señal: Calculando...")
        self.lbl_band = QLabel("Banda/Canal: Calculando...")
        self.lbl_ip = QLabel("IP Local: Calculando...")

        status_layout.addWidget(self.lbl_adapter)
        status_layout.addWidget(self.lbl_ssid)
        status_layout.addWidget(self.lbl_signal)
        status_layout.addWidget(self.lbl_band)
        status_layout.addWidget(self.lbl_ip)

        layout.addWidget(status_group)

        # Quality Indicators Group
        quality_group = QGroupBox("Indicadores de Calidad")
        quality_layout = QVBoxLayout(quality_group)

        self.lbl_latency = QLabel("Latencia Mediana: -- ms")
        self.lbl_loss = QLabel("Pérdida de Paquetes: -- %")
        self.lbl_jitter = QLabel("Jitter: -- ms")
        self.lbl_overall = QLabel("Estado Global: Evaluando...")

        quality_layout.addWidget(self.lbl_latency)
        quality_layout.addWidget(self.lbl_loss)
        quality_layout.addWidget(self.lbl_jitter)
        quality_layout.addWidget(self.lbl_overall)

        btn_refresh = QPushButton("Actualizar Mediciones Ahora")
        btn_refresh.clicked.connect(self._update_status)
        quality_layout.addWidget(btn_refresh)

        layout.addWidget(quality_group)
        layout.addStretch()

    def _setup_scanner_tab(self):
        layout = QVBoxLayout(self.scanner_tab)

        btn_scan = QPushButton("Escanear Redes Visibles")
        btn_scan.clicked.connect(self._perform_scan)
        layout.addWidget(btn_scan)

        self.table_networks = QTableWidget(0, 5)
        self.table_networks.setHorizontalHeaderLabels(["SSID", "BSSID", "Señal", "Canal", "Banda"])
        self.table_networks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_networks)

    def _setup_optimizer_tab(self):
        layout = QVBoxLayout(self.optimizer_tab)

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Modo de Operación:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Diagnóstico (Solo Lectura)", "Recomendaciones", "Optimización Controlada"])
        self.combo_mode.currentIndexChanged.connect(self._change_mode)
        mode_layout.addWidget(self.combo_mode)
        layout.addLayout(mode_layout)

        self.table_recs = QTableWidget(0, 5)
        self.table_recs.setHorizontalHeaderLabels(["Propiedad", "Actual", "Propuesto", "Beneficio", "Acción"])
        self.table_recs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_recs)

        btn_recs = QPushButton("Analizar Opciones de Mejora")
        btn_recs.clicked.connect(self._generate_recommendations)
        layout.addWidget(btn_recs)

    def _setup_reports_tab(self):
        layout = QVBoxLayout(self.reports_tab)

        btn_csv = QPushButton("Exportar Histórico a CSV")
        btn_csv.clicked.connect(self._export_csv)
        layout.addWidget(btn_csv)

        btn_json = QPushButton("Exportar Histórico y Eventos a JSON")
        btn_json.clicked.connect(self._export_json)
        layout.addWidget(btn_json)

        layout.addStretch()

    def _update_status(self):
        """Update the connection status tab."""
        interfaces = self.adapter.get_interfaces()
        if not interfaces:
             self.lbl_adapter.setText("Adaptador: No encontrado o desconectado")
             return

        iface = interfaces[0]
        name = iface.get("name", "Desconocido")
        self.lbl_adapter.setText(f"Adaptador: {name} ({iface.get('description', '')})")
        self.lbl_ssid.setText(f"SSID: {iface.get('ssid', 'Desconectado')}")
        self.lbl_signal.setText(f"Señal: {iface.get('signal', 'N/A')}")

        ch = iface.get("channel", "N/A")
        self.lbl_band.setText(f"Canal: {ch}")

        ip_conf = self.adapter.get_ip_config(name)
        ip = ip_conf.get("ip", "Desconocida")
        gw = ip_conf.get("gateway", "Desconocida")
        self.lbl_ip.setText(f"IP Local: {ip} | Puerta de enlace: {gw}")

        # Get recent metrics from DB if monitor is running
        metrics = self.db.get_metrics(limit=1)
        if metrics:
             m = metrics[0]
             lat = m.get("latency_median")
             loss = m.get("packet_loss")
             jit = m.get("jitter")

             self.lbl_latency.setText(f"Latencia Mediana: {lat:.1f} ms" if lat else "Latencia Mediana: -- ms")
             self.lbl_loss.setText(f"Pérdida de Paquetes: {loss:.1f} %" if loss is not None else "Pérdida de Paquetes: -- %")
             self.lbl_jitter.setText(f"Jitter: {jit:.1f} ms" if jit else "Jitter: -- ms")

             # Simple overall calculation
             if loss is not None and loss > 5.0:
                  self.lbl_overall.setText("Estado Global: Malo (Pérdida de paquetes)")
                  self.lbl_overall.setStyleSheet("color: red; font-weight: bold;")
             elif lat is not None and lat > 100.0:
                  self.lbl_overall.setText("Estado Global: Regular (Latencia alta)")
                  self.lbl_overall.setStyleSheet("color: orange; font-weight: bold;")
             elif lat is not None:
                  self.lbl_overall.setText("Estado Global: Excelente")
                  self.lbl_overall.setStyleSheet("color: green; font-weight: bold;")

    def _perform_scan(self):
        """Run Wi-Fi scan and populate table."""
        self.table_networks.setRowCount(0)
        networks = self.scanner.scan_networks()
        for i, net in enumerate(networks):
             self.table_networks.insertRow(i)
             self.table_networks.setItem(i, 0, QTableWidgetItem(net.get("ssid", "")))
             self.table_networks.setItem(i, 1, QTableWidgetItem(net.get("bssid", "")))
             self.table_networks.setItem(i, 2, QTableWidgetItem(net.get("signal", "")))
             self.table_networks.setItem(i, 3, QTableWidgetItem(net.get("channel", "")))
             self.table_networks.setItem(i, 4, QTableWidgetItem(net.get("band", "")))

    def _change_mode(self, index):
        mode_map = {0: OptimizerMode.DIAGNOSTIC, 1: OptimizerMode.RECOMMENDATION, 2: OptimizerMode.OPTIMIZATION}
        self.optimizer.set_mode(mode_map.get(index, OptimizerMode.RECOMMENDATION))

    def _generate_recommendations(self):
        interfaces = self.adapter.get_interfaces()
        if not interfaces:
             QMessageBox.warning(self, "Error", "No se encontró adaptador activo.")
             return

        name = interfaces[0].get("name", "Wi-Fi")
        props = self.adapter.get_adapter_properties(name)
        recs = self.optimizer.get_recommendations(name, props)

        self.table_recs.setRowCount(0)
        for i, rec in enumerate(recs):
             self.table_recs.insertRow(i)
             self.table_recs.setItem(i, 0, QTableWidgetItem(rec["property"]))
             self.table_recs.setItem(i, 1, QTableWidgetItem(str(rec["current"])))
             self.table_recs.setItem(i, 2, QTableWidgetItem(str(rec["proposed"])))
             self.table_recs.setItem(i, 3, QTableWidgetItem(rec["benefit"]))

             btn_apply = QPushButton("Aplicar")
             # Capture variables correctly in lambda
             btn_apply.clicked.connect(lambda checked=False, r=rec, n=name: self._apply_rec(n, r))

             if self.optimizer.mode != OptimizerMode.OPTIMIZATION:
                  btn_apply.setEnabled(False)
                  btn_apply.setToolTip("Cambie al modo Optimización para aplicar.")

             self.table_recs.setCellWidget(i, 4, btn_apply)

    def _apply_rec(self, adapter_name, rec):
        reply = QMessageBox.question(
            self, "Confirmar Optimización",
            f"¿Desea cambiar '{rec['property']}' de '{rec['current']}' a '{rec['proposed']}'?\n\nBeneficio: {rec['benefit']}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
             success, msg = self.optimizer.apply_optimization(adapter_name, rec["property"], rec["proposed"], rec["current"])
             if success:
                  QMessageBox.information(self, "Éxito", "Optimización aplicada correctamente.")
                  self._generate_recommendations() # Refresh
             else:
                  QMessageBox.critical(self, "Error", f"No se pudo aplicar: {msg}")

    def _export_csv(self):
        # En una aplicación real usaríamos QFileDialog
        filename = "wifi_report.csv"
        success, msg = self.exporter.export_to_csv(filename)
        if success:
             QMessageBox.information(self, "Exportación", msg)
        else:
             QMessageBox.warning(self, "Exportación Fallida", msg)

    def _export_json(self):
        filename = "wifi_report.json"
        success, msg = self.exporter.export_to_json(filename)
        if success:
             QMessageBox.information(self, "Exportación", msg)
        else:
             QMessageBox.warning(self, "Exportación Fallida", msg)

    def closeEvent(self, event):
        """Handle application exit."""
        self.monitor.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
