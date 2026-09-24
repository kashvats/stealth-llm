#!/bin/bash
# MacOS/Linux startup script for Stealth Pilot

OS_NAME=$(uname -s)

# Dependency Check for Linux
if [[ "$OS_NAME" == "Linux" ]]; then
    if ! command -v xclip &> /dev/null && ! command -v xsel &> /dev/null; then
        echo "WARNING: xclip/xsel not found. Clipboard monitoring might fail."
        echo "Please run: sudo apt-get install xclip portaudio19-dev python3-pyaudio python3-tk"
    fi
fi

# Check if virtualenv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtualenv
source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the application
echo "Starting Stealth Pilot..."
python3 main.py
