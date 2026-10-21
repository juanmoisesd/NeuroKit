import PyInstaller.__main__
import platform
import os

def build():
    print("Starting build process for WiFi Performance Manager...")

    is_windows = platform.system().lower() == "windows"
    separator = ";" if is_windows else ":"

    # Base arguments for PyInstaller
    args = [
        'src/main.py',
        '--name=WiFiPerformanceManager',
        '--onedir',
        '--windowed',
        '--clean',
        f'--add-data=src{separator}src', # Need to ensure src modules are included
    ]

    if is_windows:
         # Add Windows specific options (icon, UAC)
         # Note: Icon should be placed in assets/icon.ico
         args.append('--uac-admin') # Request admin privileges for network changes
         if os.path.exists('assets/icon.ico'):
             args.append('--icon=assets/icon.ico')

    PyInstaller.__main__.run(args)
    print("Build complete. Executable is in the 'dist' folder.")

if __name__ == "__main__":
    build()
