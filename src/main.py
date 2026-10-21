import sys
import logging
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("wifi_manager.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting WiFi Performance Manager...")

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("WiFi Performance Manager")
    app.setOrganizationName("UNIR")
    app.setOrganizationDomain("unir.net")

    # Initialize and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
