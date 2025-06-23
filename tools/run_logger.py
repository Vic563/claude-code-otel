#!/usr/bin/env python3
"""
Wrapper script for background logger that automatically uses the virtual environment.
"""
import subprocess
import sys
from pathlib import Path

# Use the virtual environment Python
venv_python = Path(__file__).parent.parent / "venv_observability" / 'Scripts' if platform.system() == 'Windows' else 'bin' / "python"

if not venv_python.exists():
    print("❌ Virtual environment not found. Run 'python setup_observability.py' first.")
    sys.exit(1)

# Run the actual logger with virtual environment Python
logger_script = Path(__file__).parent / "logger" / "background_logger.py"
cmd = [str(venv_python), str(logger_script)] + sys.argv[1:]

subprocess.run(cmd)
