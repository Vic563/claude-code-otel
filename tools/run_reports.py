#!/usr/bin/env python3
"""
Wrapper script for report generator that automatically uses the virtual environment.
"""
import subprocess
import sys
from pathlib import Path

# Use the virtual environment Python
venv_python = Path(__file__).parent.parent / "venv_observability" / 'Scripts' if platform.system() == 'Windows' else 'bin' / "python"

if not venv_python.exists():
    print("❌ Virtual environment not found. Run 'python setup_observability.py' first.")
    sys.exit(1)

# Run the actual report generator with virtual environment Python
reports_script = Path(__file__).parent / "reports" / "generate_reports.py"
cmd = [str(venv_python), str(reports_script)] + sys.argv[1:]

subprocess.run(cmd)
