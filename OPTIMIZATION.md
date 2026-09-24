# 🚀 Silent Strategist - RAM Optimization Guide

This guide helps you run Silent Strategist on **8GB RAM devices** without lag or crashes.

---

## 📊 RAM Requirements by Configuration

| Configuration | Min RAM | Recommended | Notes |
|---|---|---|---|
| **Ollama (1B model)** | 4GB | 8GB | Lightweight, portable |
| **Ollama (3-7B model)** | 12GB | 16GB | Better quality, heavier |
| **OpenAI (Cloud)** | 1GB | 2GB | Minimal local RAM, internet required |
| **Code Validation** | +2GB | +4GB | Sandbox overhead |

---

## ⚡ 8GB RAM Setup (Optimal)

### Step 1: Install Ultra-Lightweight Model

```bash
# Download tiny Llama (2.2GB download, ~2GB VRAM)
ollama pull llama3.2:1b

# Or even lighter option
ollama pull phi:latest
```

### Step 2: Create .env with 8GB Profile

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
ENABLE_CODE_VALIDATION=false
WHISPER_MODEL=tiny.en
OLLAMA_KEEP_ALIVE=300
```

### Step 3: Start Ollama with Memory Limit

```bash
# Windows: Run Ollama with limited GPU memory
set CUDA_VISIBLE_DEVICES=0

# Then start Ollama in background
ollama serve
```

### Step 4: Run Silent Strategist

```bash
python main.py
```

---

## 🔧 RAM Optimization Checklist

### Disable Heavy Features

- [ ] Set `ENABLE_CODE_VALIDATION=false` (saves ~1.5GB)
- [ ] Use `WHISPER_MODEL=tiny.en` instead of `base.en` (saves ~0.5GB)
- [ ] Set `OLLAMA_KEEP_ALIVE=300` (unloads model after 5 min idle)

### Close Background Apps

- [ ] Close Chrome, Spotify, Discord (each uses 0.5-2GB)
- [ ] Disable unused Windows services
- [ ] Close IDE/text editors if not needed

### Use Cloud Alternative (Zero Local RAM)

If local models won't fit, use OpenAI:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Then Silent Strategist uses only **50MB local RAM** (internet required).

---

## 📈 Model Comparison (8GB Context)

| Model | Size | VRAM | Speed | Quality |
|---|---|---|---|---|
| **llama3.2:1b** ⭐ | 2.2GB | ~2GB | Instant | Good |
| **phi:latest** | 2.6GB | ~2.5GB | Fast | Very Good |
| **mistral:latest** | 4.1GB | ~4GB | Medium | Excellent |
| **llama3.1:8b** | 4.7GB | ~6GB | Slow | Expert |
| **GPT-4o-mini (Cloud)** | - | 0MB | ~2s | Best |

**For 8GB**: Use **llama3.2:1b** ✅

---

## 🎯 Performance Tips

### 1. Reduce Model Context Window

Edit `llm_client.py` to lower context:

```python
# Current: 4096 tokens
# For 8GB, reduce to:
max_tokens = 1024  # Smaller responses, faster
```

### 2. Cache Aggressively

Ensure `dsa.json` is up-to-date with your common questions:

```bash
# Add high-frequency questions to dsa.json
# This prevents LLM calls entirely (instant response)
```

### 3. Use History Sparingly

The app keeps **10 Q&A pairs** in memory. For 8GB:

```python
# In main.py line 93:
self.max_history = 5  # Reduce from 10 to 5
```

### 4. Disable Audio (if not needed)

Comment out in `main.py`:

```python
# self.audio_transcriber = AudioTranscriber(...)
# self.audio_transcriber.start()
```

Saves **~200MB RAM**.

---

## 📉 Memory Monitoring

### Check RAM Usage During Runtime

```bash
# In PowerShell
Get-Process python | ForEach-Object { $_.WorkingSet64 / 1GB }

# Or use Task Manager
# Ctrl+Shift+Esc → Processes → Python process
```

### RAM Usage Breakdown (8GB Mode)

- Windows/System: **~2GB**
- Silent Strategist: **~1.5GB**
  - Ollama model: ~2GB (separate process)
  - UI + Whisper: ~0.5GB
- Available headroom: **~2GB**

---

## 🐛 Troubleshooting Low-RAM Issues

### Issue: "Out of Memory" Error

**Solution:**
1. Close all other apps
2. Reduce `OLLAMA_KEEP_ALIVE` to 60 (unload after 1 min)
3. Use `llama3.2:1b` instead of larger model
4. Disable code validation

### Issue: Audio Transcription Hangs

**Solution:**
```env
WHISPER_MODEL=tiny.en   # Fastest, smallest
# Or disable entirely in main.py
```

### Issue: App Crashes on Startup

**Solution:**
1. Check available RAM: `wmic OS get TotalVisibleMemorySize`
2. Close other apps to free 2GB minimum
3. Run as Administrator
4. Restart Ollama service

---

## ✅ Validation Checklist

Test your 8GB setup:

- [ ] Ollama loads `llama3.2:1b` without freezing
- [ ] First question takes <5 seconds
- [ ] Subsequent cached questions are instant
- [ ] No OOM (out of memory) errors
- [ ] Overlay responsive to clicks
- [ ] History navigation works smoothly

---

## 🚀 Future Improvements

Coming soon for better 8GB support:

- [ ] Quantized models (4-bit compression, 50% smaller)
- [ ] Streaming responses (show answer as it's generated)
- [ ] Knowledge base indexing (faster lookup)
- [ ] Lazy audio loading (only when needed)

---

## 📞 Still Having Issues?

1. Check `config.json` for correct settings
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check logs: Look for error messages in console
4. Try OpenAI mode (eliminates local model RAM entirely)
5. Open issue on [GitHub](https://github.com/kashvats/stealth-llm/issues)

---

**Your 8GB laptop can run Silent Strategist. Let's make it work! 💪**
