import os
import pandas as pd
import numpy as np

def analyze(filepath):
    """
    Generates a basic statistical summary or text preview of a file.
    """
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    result = f"Analysis of {filename}\n"
    result += "=" * (12 + len(filename)) + "\n\n"

    try:
        if ext == '.csv':
            df = pd.read_csv(filepath)
            result += "Type: CSV Table\n"
            result += f"Shape: {df.shape}\n\n"
            result += "Summary Statistics:\n"
            result += df.describe(include='all').to_string()
        elif ext in ['.txt', '.dat']:
            try:
                # Try loading as numeric signal
                data = np.loadtxt(filepath)
                result += "Type: Signal Data\n"
                result += f"Length: {len(data)}\n\n"
                result += pd.Series(data).describe().to_string()
            except:
                # Fallback to text preview
                with open(filepath, 'r', errors='ignore') as f:
                    lines = f.readlines()
                    result += "Type: Text File\n"
                    result += f"Lines: {len(lines)}\n\nContent Preview (first 20 lines):\n"
                    result += "".join(lines[:20])
        else:
            stats = os.stat(filepath)
            result += f"Type: Binary/Other ({ext})\n"
            result += f"Size: {stats.st_size} bytes\n"

    except Exception as e:
        result += f"Error during analysis: {e}"

    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(analyze(sys.argv[1]))
