# Stealth Pilot v2.5

A powerful, stealthy AI assistant designed for online meetings, coding interviews, and real-time strategic support. Stealth Pilot features a transparent overlay, high-fidelity voice transcription, and multi-modal interaction (Voice, Clipboard, DSA).

## 🚀 Key Features

-   **🎤 Real-time Voice Transcription**: Local, offline transcription using `faster-whisper`. Detects speech from meeting speakers (loopback) or microphone.
-   **👻 Stealth Overlay**: Designed to be invisible to screen-sharing software (Windows). Features a click-through, minimal UI with rich themes.
-   **📋 Clipboard Auto-Solver**: Monitors clipboard for code snippets, data patterns, or problem statements and provides instant solutions.
-   **⚡ DSA Quick Solve**: Dedicated mode for Data Structures & Algorithms with professional explanations and clean implementations.
-   **🔒 Secure Lock System**: Flexible locking mechanism including "Absolute Lock" (BUNK mode) to halt all AI updates for manual note-taking.
-   **🌍 Multi-lingual Support**: Supports 10+ programming languages and specific "Interview" personas.
-   **📂 Resume Context**: Automatically leverages `Resume.pdf` or `resume_text.txt` to personalize responses.

## 🛠️ Setup

### Prerequisites
-   Python 3.10+
-   [Ollama](https://ollama.com/) (for local LLM support)

### Installation
1.  **Clone the repository and install dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```
2.  **Configure Environment Variables**:
    Create a `.env` file or set variables directly:
    ```powershell
    $env:OPENAI_API_KEY="sk-..."    # Optional: For Cloud Mode
    $env:LLM_PROVIDER="ollama"      # 'ollama' or 'openai'
    $env:OLLAMA_MODEL="llama3.2"
    ```
3.  **Prepare Context**:
    Place `Resume.pdf` in the root directory. It will be automatically parsed for context.

## ⌨️ Hotkeys

| Key Combo | Action |
| :--- | :--- |
| `Ctrl+Shift+V` | Toggle Listening ON/OFF |
| `Ctrl+Shift+C` | Trigger Clipboard Solve |
| `Ctrl+Shift+D` | Trigger DSA Mode |
| `Ctrl+Shift+L` | Absolute Lock (BUNK Mode) |
| `Ctrl+Shift+U` | Unlock System |
| `Ctrl+Shift+G` | Cycle Programming Language |
| `Ctrl+Shift+R` | Rescan Audio Devices |
| `Ctrl+Shift+X` | Emergency Stop (Close App) |

## 🖱️ UI Controls

-   **MODE**: Toggles between Local (Ollama) and Cloud (OpenAI).
-   **VOICE**: Enables/Disables real-time transcription.
-   **PASTE**: Manually triggers clipboard processing.
-   **DSA**: Triggers optimized DSA solver.
-   **CLEAR**: Resets conversation history and clears the UI.
-   **NOTE**: Toggles "Notepad Mode" for manual editing.
-   **COPY**: Copies the last AI response to your clipboard.

## ⚖️ Usage Modes

### 1. The Strategist (Voice-First)
Simply join a meeting and enable "VOICE". Stealth Pilot will listen, detect questions, and provide answers in the overlay.

### 2. The Pilot (Clipboard-Monitor)
Enable "CLIPBOARD" monitoring. Copy any problem or question to your clipboard, and the overlay will update instantly with a solution.

### 3. The Scholar (DSA Mode)
Use the DSA button or hotkey to get deep-dive architectural explanations and optimized code implementations.

## ⚠️ Notes
-   **Audio Scan**: At startup, the app scans for active signals. Ensure your meeting audio is playing before starting or use `Ctrl+Shift+R` to rescan.
-   **Stealth**: The overlay uses `customtkinter` and specific Windows flags to remain invisible to captures. Ensure "Stealth" is indicated in the status label.
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
