# Claude Code Observability - Plug & Play Setup Guide

## 🚀 Quick Start (One Command Setup)

The observability tools are now completely plug-and-play! Just run:

```bash
make setup-observability
```

This single command will:
- ✅ Check Python version compatibility (3.8+)
- ✅ Create an isolated virtual environment
- ✅ Install all required dependencies automatically
- ✅ Create activation scripts for easy use
- ✅ Verify the installation works
- ✅ Show you exactly what to do next

## 📦 What Gets Installed

### Automatic Virtual Environment
- `venv_observability/` - Isolated Python environment (won't affect your system)
- All dependencies installed inside this environment
- No conflicts with existing Python packages

### Dependencies Auto-Installed
- **Core**: `sqlite3` (usually built-in), `csv`, `json`
- **PDF Generation**: `reportlab` for beautiful PDF reports
- **Setup Tools**: `setuptools` for package management
- **Optional**: `pytest` for testing (if available)

### Scripts Created
- `activate_observability.sh` - Easy environment activation (Unix/Linux/Mac)
- `activate_observability.bat` - Easy environment activation (Windows)
- Smart wrapper scripts that automatically use the virtual environment

## 🎯 Zero-Configuration Usage

After running `make setup-observability`, everything works automatically:

```bash
# Start collecting observability data
make start-logger

# Generate cost reports
make generate-cost-report

# Generate user activity reports  
make generate-user-report

# Test with sample data
make test-observability
```

**No need to activate environments or install dependencies manually!**

## 🔧 Alternative Setup Methods

### Method 1: Manual Virtual Environment (Advanced Users)
```bash
# Create virtual environment manually
python -m venv venv_observability

# Activate it
source venv_observability/bin/activate  # Unix/Linux/Mac
# OR
venv_observability\Scripts\activate.bat  # Windows

# Install dependencies
pip install reportlab setuptools

# Run tools
make start-logger
```

### Method 2: System-Wide Installation (Not Recommended)
```bash
# Install dependencies globally (may cause conflicts)
pip install -r tools/requirements.txt

# Use legacy commands
make install-observability-tools
```

## 🛠️ Troubleshooting

### "Virtual environment not found"
Run the setup command:
```bash
make setup-observability
```

### "Python version too old"
Update Python to 3.8 or newer:
```bash
# Check current version
python --version

# Update Python (varies by system)
# On macOS with Homebrew:
brew install python@3.11

# On Ubuntu:
sudo apt update && sudo apt install python3.11
```

### "Permission denied" on scripts
Make scripts executable:
```bash
chmod +x activate_observability.sh
chmod +x setup_observability.py
```

### Dependencies won't install
Try upgrading pip first:
```bash
python -m pip install --upgrade pip
make setup-observability
```

### "reportlab not found" (PDF generation)
The setup will auto-install reportlab, but if it fails:
```bash
# Activate the environment and install manually
source venv_observability/bin/activate
pip install reportlab
```

## 📊 Quick Test

Verify everything works:
```bash
# Check if setup is complete
make check-observability-setup

# Run a complete test
make test-observability
```

## 🔄 Updating Dependencies

To update dependencies or add new ones:
```bash
# Remove the old environment
rm -rf venv_observability

# Run setup again
make setup-observability
```

## 💡 Pro Tips

### 1. One-Time Setup
Run `make setup-observability` once per machine/project. The virtual environment persists until you delete it.

### 2. No Activation Needed
All `make` commands automatically use the virtual environment - no need to activate manually.

### 3. Check Status Anytime
```bash
make check-observability-setup
```

### 4. Environment Activation (Optional)
If you want to run Python commands directly:
```bash
# Unix/Linux/Mac
source activate_observability.sh

# Windows
activate_observability.bat
```

### 5. Clean Reinstall
```bash
# Remove environment and start fresh
rm -rf venv_observability activate_observability.*
make setup-observability
```

## 🎉 What's New vs. Previous Version

| Before | Now |
|--------|-----|
| Manual `pip install -r requirements.txt` | Automatic dependency installation |
| System-wide Python dependencies | Isolated virtual environment |
| Manual dependency checking | Auto-install missing packages |
| Complex setup instructions | Single command: `make setup-observability` |
| Environment activation required | Commands work automatically |
| Dependency conflicts possible | Zero conflicts (isolated environment) |

## 🚨 Migrating from Old Setup

If you previously installed dependencies manually:

1. **Clean up old installation** (optional):
   ```bash
   pip uninstall reportlab setuptools  # Only if installed globally
   ```

2. **Run new setup**:
   ```bash
   make setup-observability
   ```

3. **Use new commands** (they work the same but better):
   ```bash
   make start-logger          # Now uses virtual environment automatically
   make generate-cost-report  # Faster, more reliable
   ```

The new system is backward compatible - existing data and reports will work perfectly!