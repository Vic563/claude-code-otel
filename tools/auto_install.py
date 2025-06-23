#!/usr/bin/env python3
"""
Auto-installer module for Claude Code observability tools.

This module automatically checks for and installs missing dependencies
when the observability tools are used, making them truly plug-and-play.
"""

import importlib
import subprocess
import sys
from pathlib import Path

def check_and_install_dependency(package_name, import_name=None, description=None):
    """
    Check if a dependency is available and install it if missing.
    
    Args:
        package_name: The pip package name
        import_name: The import name (if different from package_name)
        description: Human-readable description of the dependency
    
    Returns:
        bool: True if dependency is available, False if installation failed
    """
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        print(f"⚠️  Missing dependency: {description or package_name}")
        print(f"🔧 Installing {package_name}...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ Installed {package_name}")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package_name}")
            print(f"💡 Try running: pip install {package_name}")
            return False

def ensure_dependencies():
    """
    Ensure all required dependencies are available.
    Auto-install missing dependencies with user permission.
    """
    print("🔍 Checking dependencies...")
    
    dependencies = [
        ("reportlab", "reportlab.pdfgen.canvas", "PDF generation"),
        ("setuptools", "setuptools", "Package management tools"),
    ]
    
    # Check if we should auto-install
    auto_install = True
    
    missing_deps = []
    for package_name, import_name, description in dependencies:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing_deps.append((package_name, import_name, description))
    
    if not missing_deps:
        print("✅ All dependencies are available")
        return True
    
    # Ask for permission to auto-install
    if auto_install:
        print(f"\n📦 Found {len(missing_deps)} missing dependencies:")
        for package_name, _, description in missing_deps:
            print(f"   • {package_name} ({description})")
        
        response = input("\n🤔 Auto-install missing dependencies? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            print("🚀 Installing dependencies...")
            
            all_installed = True
            for package_name, import_name, description in missing_deps:
                if not check_and_install_dependency(package_name, import_name, description):
                    all_installed = False
            
            if all_installed:
                print("✅ All dependencies installed successfully!")
                return True
            else:
                print("❌ Some dependencies could not be installed")
                return False
        else:
            print("⏭️  Skipping auto-installation")
            return False
    
    return False

def check_virtual_environment():
    """
    Check if we're in the observability virtual environment and guide user if not.
    """
    venv_path = Path.cwd() / "venv_observability"
    
    if venv_path.exists():
        # Check if current Python is from the virtual environment
        current_python = Path(sys.executable)
        venv_python_dir = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        
        if venv_python_dir in current_python.parents:
            print("✅ Using observability virtual environment")
            return True
        else:
            print("⚠️  Virtual environment available but not activated")
            print("💡 To activate:")
            if sys.platform == "win32":
                print("   activate_observability.bat")
            else:
                print("   source activate_observability.sh")
            print("💡 Or use: make setup-observability")
            return False
    else:
        print("⚠️  Virtual environment not found")
        print("💡 Run: python setup_observability.py")
        print("💡 Or use: make setup-observability")
        return False

if __name__ == "__main__":
    # Test the auto-installer
    print("🧪 Testing auto-installer...")
    ensure_dependencies()
    check_virtual_environment()