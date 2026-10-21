"""Script para construir el ejecutable autónomo y empaquetado del instalador."""

import os
import sys
import subprocess
from pathlib import Path


def build():
    print("=== Compilando Safe Debloat Manager para Windows 10 x64 ===")
    installer_dir = Path(__file__).parent.resolve()
    root_dir = installer_dir.parent.parent.resolve()
    spec_file = installer_dir / "safe_debloat_manager.spec"

    # Verificar disponibilidad de PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller no está instalado. Ejecute 'pip install pyinstaller' para empaquetar el .exe")
        return False

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        str(spec_file),
        "--distpath",
        str(installer_dir / "dist"),
        "--workpath",
        str(installer_dir / "build"),
    ]

    print(f"Ejecutando comando: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(root_dir))
    if res.returncode == 0:
        print("\n¡Compilación exitosa! Ejecutable creado en:")
        print(installer_dir / "dist" / "SafeDebloatManager.exe")
        return True
    else:
        print("\nError durante la compilación con PyInstaller.")
        return False


if __name__ == "__main__":
    build()
