# 🕵️‍♂️ Silent Strategist

**Silent Strategist** is an elite, AI-powered assistant designed to provide discreet, high-performance support during technical interviews. It combines a local high-speed knowledge base with advanced Large Language Models (LLMs) to deliver accurate, verified solutions with zero friction.

## 🌟 The Vision

The project solves three main problems in interview assistance:
1. **Latency**: "Cache-First" architecture delivers cached solutions in milliseconds
2. **Reliability**: Built-in Code Validation Loop self-corrects LLM-generated code
3. **Stealth**: Minimal overlay stays out of the way while providing critical data

---

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Usage](#usage)
- [Security](#security)
- [Development](#development)

---

## 🛠️ Installation

### Requirements

- **Python 3.8+**
- **Windows 10+** (for native hotkey support)
- **8GB RAM minimum** (16GB+ recommended for models)

### Step 1: Clone & Install Dependencies

```bash
git clone https://github.com/kashvats/stealth-llm.git
cd stealth-llm

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Environment

Create a `.env` file in the project root:

```env
# LLM Configuration
LLM_PROVIDER=ollama                    # "ollama" or "openai"
OLLAMA_BASE_URL=http://localhost:11434 # Ollama server URL
OLLAMA_MODEL=llama3.2                  # Local model name
OPENAI_API_KEY=your-api-key-here       # Required only if using OpenAI
OPENAI_MODEL=gpt-4o-mini               # OpenAI model to use

# Code Validation
ENABLE_CODE_VALIDATION=false           # Set to true to enable sandbox validation
VALIDATION_TIMEOUT=5                   # Seconds to allow code execution

# Audio
WHISPER_MODEL=tiny.en                  # Whisper model size
```

### Step 3: Set Up Local LLM (Optional but Recommended)

Install **Ollama** for offline AI:
1. Download from [ollama.ai](https://ollama.ai)
2. Run: `ollama pull llama3.2` (1B model, lightweight)
3. Keep Ollama running in background while using Silent Strategist

### Step 4: Run the Application

```bash
python main.py
```

A transparent overlay window will appear on your screen.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | Choose `ollama` (local) or `openai` (cloud) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `llama3.2` | Model to use with Ollama |
| `OPENAI_API_KEY` | (none) | Required for OpenAI mode |
| `OPENAI_MODEL` | `gpt-4o-mini` | GPT model to use |
| `ENABLE_CODE_VALIDATION` | `false` | Enable sandbox code execution validation |

### config.json

Persists UI preferences (language, theme, LLM mode):

```json
{
  "language": "Python",
  "color_theme": "Green",
  "llm_mode": "local"
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│        Silent Strategist App            │
└─────────────────────────────────────────┘
         ↓              ↓              ↓
    ┌────────┐   ┌────────────┐   ┌─────────┐
    │ Hotkey │   │ Clipboard  │   │  Audio  │
    │Handler │   │ Monitor    │   │Transcr. │
    └────────┘   └────────────┘   └─────────┘
         ↓              ↓              ↓
    ┌──────────────────────────────────────┐
    │     Lock Manager (State Control)     │
    └──────────────────────────────────────┘
                     ↓
    ┌──────────────────────────────────────┐
    │    Knowledge Base (Local Cache)      │
    │  • dsa.json (100+ questions)         │
    │  • algorithms.json (golden code)     │
    │  • Fuzzy-match lookup                │
    └──────────────────────────────────────┘
                     ↓
    ┌──────────────────────────────────────┐
    │        LLM Client Selection           │
    │  • Try: Ollama (local, free)         │
    │  • Fallback: OpenAI (cloud, paid)    │
    │  • Fallback: Mock (testing)          │
    └──────────────────────────────────────┘
                     ↓
    ┌──────────────────────────────────────┐
    │   Code Validator (Optional)          │
    │  • Sandbox execution (subprocess)    │
    │  • Input/Output verification         │
    │  • Auto-retry on failures            │
    └──────────────────────────────────────┘
                     ↓
    ┌──────────────────────────────────────┐
    │     Stealth Overlay UI               │
    │  • Transparent text display          │
    │  • Volume meter (audio feedback)     │
    │  • Lock indicator                    │
    │  • History navigation                │
    └──────────────────────────────────────┘
```

### Module Breakdown

| Module | Purpose |
|--------|---------|
| `main.py` | Application entry point, orchestration |
| `stealth_overlay_buttons.py` | Tkinter UI, transparent window |
| `llm_client.py` | OpenAI & Ollama API wrappers |
| `knowledge_base.py` | Local DSA registry, fuzzy lookup |
| `code_validator.py` | Sandbox code execution & validation |
| `hotkey_listener.py` | Global hotkey detection |
| `clipboard_monitor.py` | Clipboard change detection |
| `audio_transcriber.py` | Whisper-based speech-to-text |
| `lock_manager.py` | State management (locked/unlocked) |

---

## 🎮 Usage

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Alt + C** | Capture & process clipboard content |
| **Alt + S** | Manual solve (prompt LLM) |
| **Alt + Left** | Previous answer in history |
| **Alt + Right** | Next answer in history |
| **Alt + L** | Toggle absolute lock (pause/resume) |
| **Alt + M** | Toggle LLM mode (Ollama ↔ OpenAI) |
| **Alt + V** | Toggle clipboard monitoring |
| **Alt + Z** | Emergency stop |

### Workflow

1. **Copy interview question** to clipboard (e.g., from LeetCode, interview platform)
2. **Hit Alt+C** or let auto-capture trigger
3. App checks **local knowledge base** → instant response if cached
4. If not cached, **queries LLM** → generates solution
5. If code validation enabled, **runs & validates** → auto-fixes if needed
6. **Displays result** in overlay (answer + `[X]` token for stealth)
7. **Alt+Left/Right** to navigate answer history

---

## 🔒 Security & Privacy

### Local-First Architecture

- **All processing offline** using Ollama (optional)
- **No data sent** to external services (unless using OpenAI)
- **Code runs in isolated subprocess** (not `eval()`)

### Code Validation Safety

- Uses **subprocess sandbox** instead of `exec()` for untrusted code
- **Timeout protection** (5-second default limit)
- **Output size capping** (1KB max returned)

### Logs & Privacy

- Logs saved locally to `interview_logs/` (never uploaded)
- Set `ENABLE_CODE_VALIDATION=false` to skip execution logs
- Clear logs anytime: `rm interview_logs/*`

---

## 🧪 Development & Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest -v

# Run specific test suite
pytest test_code_validator.py -v
pytest test_llm_client.py -v
pytest test_knowledge_base.py -v
```

### Project Structure

```
stealth-llm/
├── main.py                      # Main app
├── *.py                         # Module files
├── test_*.py                    # Unit tests
├── dsa.json                     # Question cache
├── algorithms.json              # Golden solutions
├── config.json                  # User settings
├── interview_logs/              # Q&A history (local)
├── .env                         # Environment config
└── requirements.txt             # Dependencies
```

### Contributing

All code is tested with `pytest`. Before submitting:

1. Run tests: `pytest -v`
2. Check no silent exception handlers (use specific `except` clauses)
3. Add logging for errors: `logger.error(f"Specific message: {e}")`
4. Test with both Ollama and OpenAI modes

---

## 🐛 Troubleshooting

### Ollama Not Connecting

```bash
# Ensure Ollama is running
ollama serve

# Test connection
curl http://localhost:11434/api/tags

# Check environment
set OLLAMA_BASE_URL=http://localhost:11434
```

### OpenAI API Errors

- Verify `OPENAI_API_KEY` is valid
- Check API quota on [platform.openai.com](https://platform.openai.com)
- Ensure internet connection

### Code Validation Timeouts

- Lower resource usage on your computer
- Disable `ENABLE_CODE_VALIDATION` if consistently slow
- Use smaller Ollama model (e.g., `llama3.2:1b`)

### Hotkeys Not Working

- Ensure app window is active
- Try running as Administrator
- Check Windows regional keyboard settings

---

## 📝 License & Disclaimer

This tool is for **authorized educational and interview preparation use only**. Always follow your interview platform's terms and your jurisdiction's laws.

---

## 🤝 Support

Found a bug? Have a feature request?
- Open an issue on [GitHub](https://github.com/kashvats/stealth-llm/issues)
- Check existing issues first

---

**Built with ❤️ for interview excellence.**
