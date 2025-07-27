#!/usr/bin/env python3
"""
Gold Digger AI Bot - Quick Setup Script
Automates the initial setup process for new users
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🏆 GOLD DIGGER AI BOT - QUICK SETUP 🏆               ║
    ║                                                              ║
    ║        World-Class XAU/USD Trading Bot Setup                ║
    ║        Updated for July 2025 with Latest Technologies       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Error: Python 3.9+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("   Please upgrade Python and try again")
        sys.exit(1)
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")

def create_virtual_environment():
    """Create and activate virtual environment"""
    print("\n📦 Creating virtual environment...")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
        
        # Provide activation instructions
        if platform.system() == "Windows":
            activate_cmd = "venv\\Scripts\\activate"
        else:
            activate_cmd = "source venv/bin/activate"
        
        print(f"\n🔧 To activate the virtual environment, run:")
        print(f"   {activate_cmd}")
        
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\n📚 Installing dependencies...")
    
    # Determine pip executable
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Try running manually: pip install -r requirements.txt")
        return False

def setup_environment_file():
    """Set up environment variables file"""
    print("\n🔐 Setting up environment variables...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        # Copy example file
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ .env file created from template")
        print("📝 Please edit .env file with your actual credentials")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  .env.example not found - creating basic .env file")
        create_basic_env_file()

def create_basic_env_file():
    """Create a basic .env file"""
    basic_env = """# Gold Digger AI Bot - Environment Variables
# Fill in your actual values

# Google Gemini API Key (get from: https://ai.google.dev/)
GEMINI_API_KEY=your_gemini_api_key_here

# IC Markets Demo Account
MT5_LOGIN=your_demo_account_login
MT5_PASSWORD=your_demo_account_password
MT5_SERVER=ICMarkets-Demo

# Trading Configuration
TRADING_SYMBOL=XAUUSD
MAX_DAILY_LOSS=500.00
RISK_PER_TRADE=0.01

# Logging
LOG_LEVEL=INFO
"""
    
    with open(".env", "w") as f:
        f.write(basic_env)

def check_mt5_installation():
    """Check if MetaTrader 5 is installed"""
    print("\n🔍 Checking MetaTrader 5 installation...")
    
    if platform.system() == "Windows":
        # Common MT5 installation paths on Windows
        mt5_paths = [
            "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
            "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
            "C:\\Users\\%USERNAME%\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\terminal64.exe"
        ]
        
        mt5_found = False
        for path in mt5_paths:
            if os.path.exists(path.replace("%USERNAME%", os.getenv("USERNAME", ""))):
                mt5_found = True
                break
        
        if mt5_found:
            print("✅ MetaTrader 5 installation detected")
        else:
            print("⚠️  MetaTrader 5 not found")
            print("   Please download from: https://www.metatrader5.com/en/download")
    else:
        print("⚠️  MetaTrader 5 requires Windows (or Wine/VM on Mac/Linux)")
        print("   Consider using a Windows VM or VPS for full functionality")

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE! Next Steps:")
    print("="*60)
    
    steps = [
        "1. 🏦 Set up IC Markets demo account:",
        "   → Visit: https://www.icmarkets.com/global/en/open-trading-account/demo",
        "   → Choose 'Raw Spread Demo' with MT5",
        "   → Note down login, password, and server details",
        "",
        "2. 🔑 Get Google Gemini API key:",
        "   → Visit: https://ai.google.dev/",
        "   → Create account and generate API key",
        "   → Add key to .env file",
        "",
        "3. 📝 Edit .env file with your credentials:",
        "   → Open .env in text editor",
        "   → Fill in MT5 and Gemini API details",
        "",
        "4. 🚀 Run the application:",
        "   → Activate virtual environment",
        "   → Run: streamlit run app.py",
        "",
        "5. 📊 Access dashboard:",
        "   → Open browser to: http://localhost:8501",
        "   → Start with paper trading first!",
    ]
    
    for step in steps:
        print(step)
    
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Always test on demo account first!")
    print("📚 Read README.md for detailed instructions")
    print("🆘 Need help? Check the troubleshooting section")
    print("="*60)

def main():
    """Main setup function"""
    print_banner()
    
    print("🔍 Checking system requirements...")
    check_python_version()
    
    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ Error: requirements.txt not found")
        print("   Please run this script from the project root directory")
        sys.exit(1)
    
    # Create virtual environment
    if not os.path.exists("venv"):
        if not create_virtual_environment():
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Install dependencies
    if not install_dependencies():
        print("⚠️  Dependency installation failed - you may need to install manually")
    
    # Setup environment file
    setup_environment_file()
    
    # Check MT5 installation
    check_mt5_installation()
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main()
