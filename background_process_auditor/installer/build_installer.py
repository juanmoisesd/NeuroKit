"""
Installer Build Script for Background Process Auditor.
Bundles application using PyInstaller and generates SHA256 checksum verification file.
"""

import hashlib
import os
import subprocess
import sys

def build():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    entry_point = os.path.join(repo_root, "background_process_auditor", "main.py")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "BackgroundProcessAuditor",
        "--distpath",
        dist_dir,
        entry_point
    ]

    print(f"Executing PyInstaller build command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Locate generated executable
    exe_name = "BackgroundProcessAuditor.exe" if sys.platform == "win32" else "BackgroundProcessAuditor"
    exe_path = os.path.join(dist_dir, exe_name)

    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"Executable not found at expected path: {exe_path}")

    # Compute SHA256 hash
    sha256_hash = hashlib.sha256()
    with open(exe_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    digest = sha256_hash.hexdigest()
    checksum_filepath = os.path.join(dist_dir, "VERIFICATION_CHECKSUM.sha256")

    with open(checksum_filepath, "w", encoding="utf-8") as f:
        f.write(f"{digest}  {exe_name}\n")

    print("==================================================")
    print("Build and Checksum Verification Generation Successful!")
    print(f"Executable: {exe_path}")
    print(f"SHA256 Checksum: {digest}")
    print(f"Checksum File: {checksum_filepath}")
    print("==================================================")

if __name__ == "__main__":
    build()
