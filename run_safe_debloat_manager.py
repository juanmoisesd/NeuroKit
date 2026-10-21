#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Punto de entrada principal para Safe Debloat Manager."""

import sys
import argparse
from safe_debloat_manager.gui.app import SafeDebloatApp


def main():
    parser = argparse.ArgumentParser(description="Safe Debloat Manager v1.0 - Utility para Windows 10 x64")
    parser.add_argument("--mock", action="store_true", help="Fuerza el uso de datos simulados (útil para pruebas en Linux/CI)")
    args = parser.parse_args()

    app = SafeDebloatApp(force_mock=args.mock)
    app.mainloop()


if __name__ == "__main__":
    main()
