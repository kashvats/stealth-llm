# Stealth Pilot v2

A cross-platform, stealthy AI assistant for online meetings.

## Features
- **Stealth Overlay**: Invisible to screen sharing (Windows) or minimal/click-through (all platforms).
- **Clipboard Monitor**: Instantly answers questions copied to the clipboard.
- **Caption Scraper**: Reads live captions from Google Meet, Zoom, and Teams (Web) via browser automation.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    pip install pypdf # For resume extraction
    ```

3.  **Prepare Resume (Optional)**:
    Place your `Resume.pdf` in the project root. The app will automatically extract it to `resume_text.txt` and use it for context (e.g., "Introduce yourself").
    *Alternatively, you can manually create `resume_text.txt` with your details.*

2.  **Configure LLM**:
    
    **Option A: OpenAI (High Quality)**
    Set `OPENAI_API_KEY`.
    ```powershell
    $env:OPENAI_API_KEY="sk-..."
    $env:LLM_PROVIDER="openai"
    ```

    **Option B: Ollama (Free/Local/Stealth)**
    Install [Ollama](https://ollama.com/) and pull the specific model used in `llm_offline`.
    ```powershell
    ollama pull llama3.2
    $env:LLM_PROVIDER="ollama"
    $env:OLLAMA_MODEL="llama3.2"
    ```

## Usage

### 1. Start Browser with Debugging
To enable caption scraping, you must start your browser (Chrome/Edge) with the remote debugging port open.

**Windows (PowerShell):**
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\cprofile"
```

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/cprofile"
```

**Linux (Ubuntu):**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/cprofile"
# Or if using Chromium:
chromium-browser --remote-debugging-port=9222 --user-data-dir="/tmp/cprofile"
```

**Note:** On Linux, you may need `xclip` or `xsel` for clipboard support (`sudo apt install xclip`).

### 2. Join Meeting
Join your meeting (Meet/Zoom/Teams) in this browser instance and **Enable Captions**.

### 3. Run Stealth Pilot
```bash
python main.py
```

### 4. Interact
- **Automatic**: The specific meeting context will be processed (Not fully enabled in v2 prototype).
- **Manual**: Copy any text (e.g., "What is the complexity of Quicksort?") to the clipboard. The overlay will show the answer instantly.
"# stealth-llm" 
