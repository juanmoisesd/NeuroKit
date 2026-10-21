"""Punto de entrada de módulo para Safe Debloat Manager."""

import sys
from safe_debloat_manager.gui.app import SafeDebloatApp


def main():
    force_mock = "--mock" in sys.argv
    app = SafeDebloatApp(force_mock=force_mock)
    app.mainloop()


if __name__ == "__main__":
    main()
