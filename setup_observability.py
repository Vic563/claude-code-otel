#!/usr/bin/env python3
"""
Claude Code Observability Setup Script
=====================================

This script automatically sets up the Python environment and dependencies
for the Claude Code observability tools in a plug-and-play manner.

Usage:
    python setup_observability.py
    
Or via Makefile:
    make setup-observability
"""

import os
import sys
import subprocess
import venv
import platform
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

def print_status(message, color=BLUE):
    print(f"{color}{BOLD}[SETUP]{END} {message}")

def print_success(message):
    print(f"{GREEN}{BOLD}✅ {message}{END}")

def print_warning(message):
    print(f"{YELLOW}{BOLD}⚠️  {message}{END}")

def print_error(message):
    print(f"{RED}{BOLD}❌ {message}{END}")

def run_command(command, cwd=None, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {command}")
            print_error(f"Error: {e.stderr}")
            return None
        return e

def check_python_version():
    """Check if Python version is compatible."""
    print_status("Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, but found {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment():
    """Create a virtual environment for the observability tools."""
    print_status("Setting up virtual environment...")
    
    venv_path = Path.cwd() / "venv_observability"
    
    if venv_path.exists():
        print_warning("Virtual environment already exists, skipping creation")
        return venv_path
    
    try:
        venv.create(venv_path, with_pip=True)
        print_success("Virtual environment created")
        return venv_path
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return None

def get_venv_python(venv_path):
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_dependencies(venv_path):
    """Install required dependencies in the virtual environment."""
    print_status("Installing dependencies...")
    
    python_exe = get_venv_python(venv_path)
    
    # First upgrade pip
    result = run_command(f"{python_exe} -m pip install --upgrade pip", check=False)
    if result and result.returncode != 0:
        print_warning("Could not upgrade pip, continuing...")
    
    # Install core dependencies
    core_deps = [
        "setuptools>=45.0.0",
        "reportlab>=3.6.0",  # PDF generation
        "sqlite3",  # Should be built-in but let's be explicit
    ]
    
    for dep in core_deps:
        print_status(f"Installing {dep}...")
        result = run_command(f"{python_exe} -m pip install '{dep}'", check=False)
        if result and result.returncode == 0:
            print_success(f"Installed {dep}")
        else:
            # For sqlite3, it might be built-in
            if "sqlite3" in dep:
                print_warning("sqlite3 installation failed, but may be built-in")
            else:
                print_error(f"Failed to install {dep}")
                return False
    
    # Try to install optional dependencies
    optional_deps = [
        ("pytest>=6.0.0", "Testing framework"),
        ("pytest-cov>=2.0.0", "Test coverage"),
    ]
    
    for dep, description in optional_deps:
        print_status(f"Installing optional dependency: {description}...")
        result = run_command(f"{python_exe} -m pip install '{dep}'", check=False)
        if result and result.returncode == 0:
            print_success(f"Installed {dep}")
        else:
            print_warning(f"Could not install {dep} (optional)")
    
    return True

def create_activation_script():
    """Create scripts to easily activate the environment."""
    print_status("Creating activation scripts...")
    
    # Create shell script for Unix-like systems
    if platform.system() != "Windows":
        activate_script = Path.cwd() / "activate_observability.sh"
        with open(activate_script, 'w') as f:
            f.write("""#!/bin/bash
# Claude Code Observability Environment Activation Script
echo "🚀 Activating Claude Code observability environment..."
source venv_observability/bin/activate
echo "✅ Environment activated! You can now run:"
echo "  - make start-logger"
echo "  - make generate-cost-report"
echo "  - make generate-user-report"
echo "  - make test-observability"
echo ""
echo "To deactivate: deactivate"
""")
        activate_script.chmod(0o755)
        print_success("Created activate_observability.sh")
    
    # Create batch script for Windows
    activate_script_bat = Path.cwd() / "activate_observability.bat"
    with open(activate_script_bat, 'w') as f:
        f.write("""@echo off
REM Claude Code Observability Environment Activation Script
echo 🚀 Activating Claude Code observability environment...
call venv_observability\\Scripts\\activate.bat
echo ✅ Environment activated! You can now run:
echo   - make start-logger
echo   - make generate-cost-report
echo   - make generate-user-report
echo   - make test-observability
echo.
echo To deactivate: deactivate
""")
    print_success("Created activate_observability.bat")

def create_wrapper_scripts():
    """Create wrapper scripts that automatically use the virtual environment."""
    print_status("Creating wrapper scripts...")
    
    venv_path = Path.cwd() / "venv_observability"
    python_exe = get_venv_python(venv_path)
    
    # Create wrapper for background logger
    logger_wrapper = Path.cwd() / "tools" / "run_logger.py"
    with open(logger_wrapper, 'w') as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"
Wrapper script for background logger that automatically uses the virtual environment.
\"\"\"
import subprocess
import sys
from pathlib import Path

# Use the virtual environment Python
venv_python = Path(__file__).parent.parent / "venv_observability" / {"'Scripts' if platform.system() == 'Windows' else 'bin'"} / "python{'exe' if platform.system() == 'Windows' else ''}"

if not venv_python.exists():
    print("❌ Virtual environment not found. Run 'python setup_observability.py' first.")
    sys.exit(1)

# Run the actual logger with virtual environment Python
logger_script = Path(__file__).parent / "logger" / "background_logger.py"
cmd = [str(venv_python), str(logger_script)] + sys.argv[1:]

subprocess.run(cmd)
""")
    logger_wrapper.chmod(0o755)
    
    # Create wrapper for report generator
    reports_wrapper = Path.cwd() / "tools" / "run_reports.py"
    with open(reports_wrapper, 'w') as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"
Wrapper script for report generator that automatically uses the virtual environment.
\"\"\"
import subprocess
import sys
from pathlib import Path

# Use the virtual environment Python
venv_python = Path(__file__).parent.parent / "venv_observability" / {"'Scripts' if platform.system() == 'Windows' else 'bin'"} / "python{'exe' if platform.system() == 'Windows' else ''}"

if not venv_python.exists():
    print("❌ Virtual environment not found. Run 'python setup_observability.py' first.")
    sys.exit(1)

# Run the actual report generator with virtual environment Python
reports_script = Path(__file__).parent / "reports" / "generate_reports.py"
cmd = [str(venv_python), str(reports_script)] + sys.argv[1:]

subprocess.run(cmd)
""")
    reports_wrapper.chmod(0o755)
    
    print_success("Created wrapper scripts")

def verify_installation():
    """Verify that the installation works correctly."""
    print_status("Verifying installation...")
    
    venv_path = Path.cwd() / "venv_observability"
    python_exe = get_venv_python(venv_path)
    
    # Test imports
    test_imports = [
        "sqlite3",
        "reportlab.pdfgen.canvas",
        "setuptools",
    ]
    
    for import_name in test_imports:
        result = run_command(f"{python_exe} -c 'import {import_name}; print(\"✅ {import_name}\")'", check=False)
        if result and result.returncode == 0:
            print_success(f"Verified {import_name}")
        else:
            print_error(f"Could not import {import_name}")
            return False
    
    # Test that the tools directory exists and has the required files
    tools_dir = Path.cwd() / "tools"
    required_files = [
        "logger/background_logger.py",
        "logger/database.py",
        "reports/generate_reports.py",
    ]
    
    for file_path in required_files:
        full_path = tools_dir / file_path
        if full_path.exists():
            print_success(f"Verified {file_path}")
        else:
            print_error(f"Missing required file: {file_path}")
            return False
    
    return True

def print_usage_instructions():
    """Print instructions on how to use the observability tools."""
    print(f"\n{GREEN}{BOLD}🎉 Setup Complete!{END}")
    print(f"\n{BLUE}{BOLD}Quick Start:{END}")
    print("1. Activate the environment:")
    if platform.system() == "Windows":
        print("   activate_observability.bat")
    else:
        print("   source activate_observability.sh")
    
    print("\n2. Start the observability stack:")
    print("   make up")
    
    print("\n3. Start collecting data:")
    print("   make start-logger")
    
    print("\n4. Generate reports:")
    print("   make generate-cost-report")
    print("   make generate-user-report")
    
    print(f"\n{BLUE}{BOLD}Alternative (no environment activation needed):{END}")
    print("   make setup-observability  # Run this setup script")
    print("   make start-logger         # Now works automatically!")
    print("   make generate-cost-report # Uses virtual environment automatically")
    
    print(f"\n{YELLOW}{BOLD}Files Created:{END}")
    print("   • venv_observability/     - Virtual environment")
    print("   • activate_observability.sh - Environment activation (Unix/Linux/Mac)")
    print("   • activate_observability.bat - Environment activation (Windows)")
    print("   • tools/run_logger.py     - Logger wrapper script")
    print("   • tools/run_reports.py    - Reports wrapper script")

def main():
    """Main setup function."""
    print(f"{BLUE}{BOLD}{'='*60}{END}")
    print(f"{BLUE}{BOLD}Claude Code Observability Setup{END}")
    print(f"{BLUE}{BOLD}{'='*60}{END}")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    if not venv_path:
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(venv_path):
        print_error("Failed to install dependencies")
        sys.exit(1)
    
    # Create activation scripts
    create_activation_script()
    
    # Create wrapper scripts
    create_wrapper_scripts()
    
    # Verify installation
    if not verify_installation():
        print_error("Installation verification failed")
        sys.exit(1)
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main()