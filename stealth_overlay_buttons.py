import tkinter as tk
import customtkinter as ctk
import platform
import ctypes
import logging
from typing import Optional, Callable
from CTkToolTip import CTkToolTip

logger = logging.getLogger(__name__)

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class StealthOverlayButtons:
    def __init__(self, root: tk.Tk, on_toggle_mode=None, on_voice_toggle=None, on_paste=None, on_dsa=None, on_clear=None, on_notepad_toggle=None, on_copy=None):
        self.root = root
        self.on_toggle_mode = on_toggle_mode
        self.on_voice_toggle = on_voice_toggle
        self.on_paste_cb = on_paste
        self.on_dsa_cb = on_dsa
        self.on_clear_cb = on_clear
        self.on_notepad_toggle = on_notepad_toggle
        self.on_copy_cb = on_copy
        
        self.notepad_active = False
        self.current_color_idx = 0
        self.colors = ["#00ff41", "#00ccff", "#ffcc00", "#ff4444", "#ffffff"]
        self.active_color = self.colors[0] # Phosphor Green default
        
        # Window Setup
        self.root.title("Stealth Pilot Pro")
        self._set_bottom_center_geometry(800, 250)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 1.0) # Solid contrast
        self.root.config(bg='#121212') 
        
        # --- Main Frame ---
        self.main_container = ctk.CTkFrame(
            self.root, 
            fg_color="#1a1a1a", 
            border_color="#333333", 
            border_width=2,
            corner_radius=15
        )
        self.main_container.pack(expand=True, fill='both', padx=2, pady=2)

        # --- Top Button Bar ---
        self.top_bar = ctk.CTkFrame(self.main_container, fg_color="transparent", height=50)
        self.top_bar.pack(side=tk.TOP, fill='x', padx=5, pady=(5, 0))
        self.top_bar.pack_propagate(False) # Keep height fixed
        
        # 1. LIVE Button
        self.live_btn = ctk.CTkButton(
            self.top_bar, text="🎤 LIVE", width=85, height=35,
            fg_color="#00ff41", hover_color="#00cc33",
            text_color="black", font=("JetBrains Mono", 11, "bold"),
            command=self._on_live_click
        )
        self.live_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.live_btn, message="Toggle speaker audio → LLM answers")

        # 2. PASTE Button
        self.paste_btn = ctk.CTkButton(
            self.top_bar, text="📋 PASTE", width=85, height=35,
            fg_color="#00ccff", hover_color="#0099cc",
            text_color="black", font=("JetBrains Mono", 11, "bold"),
            command=self._on_paste_click
        )
        self.paste_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.paste_btn, message="Ctrl+V DSA question → code + I/O")

        # 3. DSA Button
        self.dsa_btn = ctk.CTkButton(
            self.top_bar, text="⚡ DSA", width=80, height=35,
            fg_color="#a020f0", hover_color="#800080",
            text_color="white", font=("JetBrains Mono", 11, "bold"),
            command=self._on_dsa_click
        )
        self.dsa_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.dsa_btn, message="Two Sum → specific language logic")

        # 4. COPY Result
        self.copy_btn = ctk.CTkButton(
            self.top_bar, text="📄 COPY", width=80, height=35,
            fg_color="#ffffff", hover_color="#dddddd",
            text_color="black", font=("JetBrains Mono", 10, "bold"),
            command=self._on_copy_click
        )
        self.copy_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.copy_btn, message="Copy AI Answer to Clipboard")

        # 5. MODE Toggle
        self.mode_btn = ctk.CTkButton(
            self.top_bar, text="LOCAL", width=80, height=35,
            fg_color="#444444", hover_color="#555555",
            text_color="white", font=("JetBrains Mono", 10, "bold"),
            command=self._on_mode_click
        )
        self.mode_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.mode_btn, message="Local: Ollama | Cloud: OpenAI")

        # 6. CLEAR Button
        self.clear_btn = ctk.CTkButton(
            self.top_bar, text="🗑️ CLEAR", width=80, height=35,
            fg_color="#ffcc00", hover_color="#cc9900",
            text_color="black", font=("JetBrains Mono", 10, "bold"),
            command=self._on_clear_click
        )
        self.clear_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.clear_btn, message="Reset overlay + history")

        # 7. NOTEPAD Button
        self.notepad_btn = ctk.CTkButton(
            self.top_bar, text="📝 NOTE", width=80, height=35,
            fg_color="#444444", hover_color="#555555",
            text_color="white", font=("JetBrains Mono", 10, "bold"),
            command=self.toggle_notepad
        )
        self.notepad_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.notepad_btn, message="Toggle edit mode (Locks AI updates)")

        # 8. CLOSE Button
        self.close_btn = ctk.CTkButton(
            self.top_bar, text="❌", width=40, height=35,
            fg_color="#ff4444", hover_color="#cc0000",
            text_color="white", font=("JetBrains Mono", 12, "bold"),
            command=self.close
        )
        self.close_btn.pack(side=tk.LEFT, padx=2, expand=True)
        CTkToolTip(self.close_btn, message="Exit stealth overlay")

        # --- Text Area ---
        self.text_area = ctk.CTkTextbox(
            self.main_container, 
            fg_color="transparent", 
            text_color="#00ff41", 
            font=("JetBrains Mono", 13, "bold"), 
            wrap=tk.WORD
        )
        self.text_area.pack(expand=True, fill='both', padx=10, pady=(10, 35))
        
        # --- Status Bar ---
        self.status_bar = ctk.CTkFrame(self.main_container, fg_color="#0d0d0d", height=30, corner_radius=10)
        self.status_bar.place(relx=0.5, rely=0.98, anchor='s', relwidth=0.96)
        
        # Status Label (STEALTH/LOCK/BUNK)
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="STEALTH", 
            font=("JetBrains Mono", 10, "bold"),
            text_color="gray", width=70, cursor="hand2"
        )
        self.status_label.pack(side=tk.LEFT, padx=(10, 5))
        self.status_label.bind("<Button-1>", lambda e: self.toggle_notepad())
        CTkToolTip(self.status_label, message="Click to toggle Master Lock (Ctrl+Shift+K/L)")

        # Lang Dropdown
        self.lang_dropdown = ctk.CTkOptionMenu(
            self.status_bar,
            values=["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Auto", "Interview"],
            width=120, height=22, font=("JetBrains Mono", 10, "bold"),
            fg_color="#1a1a1a", button_color="#333333", button_hover_color="#00ff88",
            dropdown_fg_color="#1a1a1a", text_color="#00ff41",
            command=self._on_lang_change
        )
        self.lang_dropdown.pack(side=tk.LEFT, padx=5)
        self.lang_dropdown.set("Python")

        # Color Dropdown
        self.color_dropdown = ctk.CTkOptionMenu(
            self.status_bar,
            values=["Green", "Blue", "Orange", "Red", "White"],
            width=80, height=22, font=("JetBrains Mono", 10, "bold"),
            fg_color="#1a1a1a", button_color="#333333", button_hover_color="#00ff88",
            dropdown_fg_color="#1a1a1a", text_color="#00ff41",
            command=self._on_color_change
        )
        self.color_dropdown.pack(side=tk.LEFT, padx=5)
        self.color_dropdown.set("Green")
        
        # Meter
        self.meter_bar = ctk.CTkProgressBar(self.status_bar, height=6, progress_color="#00ff41", fg_color="#1a1a1a")
        self.meter_bar.pack(side=tk.RIGHT, padx=10, expand=True, fill='x')
        self.meter_bar.set(0)

        # Toast notification for silent settings changes
        self.toast_label = ctk.CTkLabel(self.main_container, text="", font=("JetBrains Mono", 10, "bold"), text_color="gray")
        self.toast_label.place(relx=0.5, rely=0.15, anchor='n')

        # Resize grip
        self.resize_grip = ctk.CTkLabel(self.main_container, text="◢", text_color="#444444", cursor="sizing")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)

        self._setup_bindings()
        self.apply_stealth()

    def _setup_bindings(self):
        for widget in [self.main_container, self.top_bar, self.status_bar]:
            widget.bind("<Button-1>", self._start_move)
            widget.bind("<B1-Motion>", self._on_move)
        
        self.resize_grip.bind("<Button-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._on_resize)

    def _start_move(self, event):
        self.x, self.y = event.x, event.y
    def _on_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def _start_resize(self, event):
        self.sw, self.sh = self.root.winfo_width(), self.root.winfo_height()
        self.sx, self.sy = event.x_root, event.y_root
    def _on_resize(self, event):
        new_w = max(200, self.sw + (event.x_root - self.sx))
        new_h = max(150, self.sh + (event.y_root - self.sy))
        self.root.geometry(f"{new_w}x{new_h}")

    def _cancel_hide_timer(self):
        """Cancels any active auto-hide timer."""
        if hasattr(self, '_hide_timer') and self._hide_timer:
            self.root.after_cancel(self._hide_timer)
            self._hide_timer = None

    def _on_live_click(self):
        self._cancel_hide_timer()
        if self.on_voice_toggle: self.on_voice_toggle()

    def set_voice_state(self, active: bool):
        if active:
            self.live_btn.configure(text="🎤 LIVE", fg_color="#00ff41", text_color="black")
        else:
            self.live_btn.configure(text="🎤 OFF", fg_color="#ff4444", text_color="white")

    def _on_paste_click(self):
        self._cancel_hide_timer()
        if self.on_paste_cb: self.on_paste_cb()

    def _on_dsa_click(self):
        self._cancel_hide_timer()
        if self.on_dsa_cb: self.on_dsa_cb()

    def _on_copy_click(self):
        self._cancel_hide_timer()
        if self.on_copy_cb: self.on_copy_cb()

    def _on_clear_click(self):
        self._cancel_hide_timer()
        if self.on_clear_cb: self.on_clear_cb()

    def _on_mode_click(self):
        self._cancel_hide_timer()
        if self.on_toggle_mode: self.on_toggle_mode()

    def set_mode_icon(self, is_online: bool):
        self._cancel_hide_timer()
        self.mode_btn.configure(text="CLOUD" if is_online else "LOCAL", 
                              fg_color="#0066cc" if is_online else "#444444")
        self.root.deiconify()
        self.root.lift()

    def _on_lang_change(self, lang):
        self._cancel_hide_timer()
        if hasattr(self, 'on_lang_cb'): self.on_lang_cb(lang)
        self.root.deiconify()
        self.root.lift()

    def set_lang_callback(self, cb): self.on_lang_cb = cb
    def set_color_callback(self, cb): self.on_color_cb = cb
    def set_language_indicator(self, lang): self.lang_dropdown.set(lang)

    def _on_color_change(self, name):
        self._cancel_hide_timer()
        color_map = {"Green":"#00ff41", "Blue":"#00ccff", "Orange":"#ffcc00", "Red":"#ff4444", "White":"#ffffff"}
        self.active_color = color_map.get(name, "#00ff41")
        self.text_area.configure(text_color=self.active_color)
        self.lang_dropdown.configure(text_color=self.active_color)
        self.color_dropdown.configure(text_color=self.active_color)
        self.root.deiconify()
        self.root.lift()
        self._show_toast(f"Theme: {name}")
        if hasattr(self, 'on_color_cb'): self.on_color_cb(name)

    def _show_toast(self, text):
        self.toast_label.configure(text=text)
        self.root.after(2000, lambda: self.toast_label.configure(text=""))

    def _set_bottom_center_geometry(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = screen_height - height - 100
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_notepad(self):
        self._cancel_hide_timer()
        # Toggle local state
        self.notepad_active = not self.notepad_active
        
        if self.notepad_active:
            self.text_area._textbox.configure(state=tk.NORMAL)
            self._show_toast("Notepad Mode: ON")
        else:
            self.text_area._textbox.configure(state=tk.DISABLED)
            self._show_toast("Notepad Mode: OFF")
        
        # Trigger global lock if callback exists
        if self.on_notepad_toggle:
            self.on_notepad_toggle()
        
        self.root.deiconify()
        self.root.lift()

    def show(self, text, duration=5):
        self.root.deiconify()
        self.root.lift()
        self.update_text(text, force=True)
        if hasattr(self, '_hide_timer') and self._hide_timer:
            self.root.after_cancel(self._hide_timer)
            self._hide_timer = None
        if duration > 0:
            self._hide_timer = self.root.after(duration*1000, self.root.withdraw)

    def update_text(self, text, force=False):
        if self.notepad_active and not force:
            return
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        # If not force and not notepad, we could disable it again, but usually it's better to keep it normal
        # to allow minor user corrections if they click in.

    def update_caption(self, text, is_final=False, force=False):
        if self.notepad_active and not force:
            return
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.configure(text_color="#008822" if not is_final else self.active_color)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    def update_meter(self, level):
        boosted = min(1.0, level * 5.0)
        self.meter_bar.set(boosted)
        self.meter_bar.configure(progress_color="#ff4444" if boosted > 0.8 else ("#ffcc00" if boosted > 0.4 else "#00ff41"))

    def set_lock_indicator(self, status):
        """Updates indicator and button text to match Master Lock state."""
        mapping = {
            "ABSOLUTE_LOCK": ("BUNK", "#ff4444"), 
            "NORMAL_LOCK": ("LOCK", "#ffcc00"),
            "UNLOCKED": ("STEALTH", "#00ff41")
        }
        label, color = mapping.get(status, ("STEALTH", "#00ff41"))
        self.status_label.configure(text=label, text_color=color)
        
        if status == "UNLOCKED":
            self.notepad_btn.configure(text="📝 NOTE", fg_color="#444444")
            self.text_area._textbox.configure(state=tk.DISABLED) 
            self.notepad_active = False
        elif status == "NORMAL_LOCK":
            self.notepad_btn.configure(text="📝 NOTE", fg_color="#444444")
            # Normal lock doesn't necessarily force notepad off
        else: # ABSOLUTE_LOCK
            self.notepad_btn.configure(text="🔒 LOCK", fg_color="#ff4444")
            self.text_area._textbox.configure(state=tk.NORMAL) 
            self.notepad_active = True
            
        self.root.deiconify()
        self.root.lift()
        logger.info(f"Lock UI Synced: {status} ({label})")

    def apply_stealth(self):
        self.root.update()
        if platform.system() == "Windows":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x11)
            except: pass
    
    def close(self):
        self.root.destroy()

if __name__ == "__main__":
    r = tk.Tk()
    o = StealthOverlayButtons(r)
    o.update_text("TEST FLOW:\n1. LIVE (Green)\n2. PASTE (Blue)\n3. DSA (Purple)\n4. LOCAL (Gray)")
    r.mainloop()
