"""Șterge fișierele intermediare la nivel de înregistrare (_work/) și cache-ul Python. Păstrează scripturile și agregatele."""
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
for d in (HERE / "_work", HERE / "__pycache__"):
    if d.exists():
        shutil.rmtree(d)
        print("deleted", d.name)
