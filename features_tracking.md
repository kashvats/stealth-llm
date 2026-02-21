# Stealth Pilot Feature & Test Log

This file tracks all active features and their verification status. Every fix is tested against this list.

## 🎤 1. Voice Interaction (LIVE)
- [x] Toggle ON/OFF via button
- [x] Toggle ON/OFF via hotkey
- [x] Partial speech display (dim green)
- [x] Final speech display (bright theme color)
- [x] Question detection (trigger LLM)
- [x] Auto-resume after LLM finishes
- [x] **Verification**: Voice capture → thinking indicator → response with language context.

## 📋 2. Clipboard & Paste (PASTE)
- [x] Process manual clipboard text (PASTE button)
- [x] Auto-monitor clipboard (if enabled)
- [x] Detect data patterns (nums=, arr=) → Provide ONLY code
- [x] Detect problem statements → Provide Arch + Code
- [x] **Verification**: Copy a LeetCode problem → click PASTE → get professional solution.

## ⚡ 3. DSA Quick Solve (DSA)
- [x] Forced DSA prompt via button
- [x] Respects selected language (Python/JS/Java)
- [x] **Verification**: Click DSA with "Two Sum" in clipboard → get specific language logic.

## 📝 4. Notepad Mode (NOTE)
- [x] Toggle edit mode (Locks AI updates)
- [x] Manual text editing in text area
- [x] Restore AI updates when toggled OFF
- [x] **Verification**: Click NOTE → type "manual notes" → ensure AI doesn't overwrite.

## ☁️ 5. LLM Mode (LOCAL/CLOUD)
- [x] Switch between Ollama (Local) and OpenAI (Cloud)
- [x] Mode-specific indicator (Gray for Local, Blue for Cloud)
- [x] **Verification**: Click Mode → verify "Thinking" speed and provider change.

## 🗑️ 6. Context Reset (CLEAR)
- [x] Reset conversation history
- [x] Clear UI text area
- [x] **Verification**: Click CLEAR → verify history reset in logs.

## 🎨 7. UI Customization & Persistence
- [x] Language Dropdown (10+ languages)
- [x] Color Theme Dropdown (5 themes)
- [x] **CRITICAL**: Stay visible during selection (No auto-hide)
- [x] Bottom-Center screen anchoring
- [x] Drag & Resize functionality
- [x] Stealth Mode (Invisible to screen capture)
- [x] **Verification**: Interact with all dropdowns → ensure window NEVER closes unexpectedly.

## 🔒 8. Security & Locks
- [x] Normal Lock (Auto-unlocks after response)
- [x] Absolute Lock (Manual unlock required)
- [x] Status Label (STEALTH/LOCK/BUNK)
- [x] **Verification**: Trigger lock → verify AI/Voice pause → verify Status text.
