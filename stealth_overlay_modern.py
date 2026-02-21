import tkinter as tk
import customtkinter as ctk
import platform
import ctypes
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class StealthOverlayModern:
    def __init__(self, root: tk.Tk, on_toggle_mode=None):
        self.root = root
        self.on_toggle_mode = on_toggle_mode
        self.notepad_active = False
        self.current_color_idx = 0
        self.colors = ["#00ff41", "#00ccff", "#ffcc00", "#ff4444", "#ffffff"]
        self.active_color = self.colors[0]
        
        # Window Setup
        self.root.title("Stealth Pilot Modern")
        self.root.geometry("400x200+10+10")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 1.0)  # Fully opaque for maximum contrast against any screen background
        self.root.config(bg='#121212') # Darker deep black for phosphor pop
        
        # Window attributes for transparency on some systems
        try:
            self.root.wm_attributes("-transparentcolor", "#1a1a1a")
        except:
            pass

        # Variables for movement
        self.x = 0
        self.y = 0
        
        # --- Main Frame (Gradient-ish dark rounded) ---
        self.main_container = ctk.CTkFrame(
            self.root, 
            fg_color="#1a1a1a", 
            border_color="#333333", 
            border_width=2,
            corner_radius=15
        )
        self.main_container.pack(expand=True, fill='both', padx=2, pady=2)
        
        # --- Top-Right Control Frame ---
        self.control_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.control_frame.place(relx=0.98, rely=0.02, anchor='ne')
        
        # Modern Buttons
        self.close_btn = ctk.CTkButton(
            self.control_frame, text="✕", width=25, height=25, 
            fg_color="#ff4444", hover_color="#cc0000",
            text_color="white", corner_radius=8, font=("Arial", 12, "bold"),
            command=self.close
        )
        self.close_btn.pack(side=tk.RIGHT, padx=2)
        
        self.notepad_btn = ctk.CTkButton(
            self.control_frame, text="✎", width=25, height=25,
            fg_color="#444444", hover_color="#555555",
            text_color="white", corner_radius=8, font=("Arial", 12),
            command=self.toggle_notepad
        )
        self.notepad_btn.pack(side=tk.RIGHT, padx=2)
        
        self.mode_btn = ctk.CTkButton(
            self.control_frame, text="🏠", width=25, height=25,
            fg_color="#333333", hover_color="#0066cc",
            text_color="white", corner_radius=8, font=("Arial", 12),
            command=self._on_toggle_click
        )
        self.mode_btn.pack(side=tk.RIGHT, padx=2)
        
        self.color_dropdown = ctk.CTkOptionMenu(
            self.control_frame,
            values=["Green", "Blue", "Orange", "Red", "White"],
            width=80,
            height=25,
            font=("Arial", 10, "bold"),
            fg_color="#333333",
            button_color="#444444",
            button_hover_color="#0066cc",
            dropdown_fg_color="#1a1a1a",
            text_color="#00ff41", # Phosphor Green default
            command=self._on_color_change
        )
        self.color_dropdown.pack(side=tk.RIGHT, padx=2)
        self.color_dropdown.set("Green")

        # --- Text Area (Modern Mono Font) ---
        self.text_area = ctk.CTkTextbox(
            self.main_container, 
            fg_color="transparent", 
            text_color="#00ff41",  # Phosphor Green
            font=("JetBrains Mono", 13, "bold"), 
            wrap=tk.WORD,
            scrollbar_button_color="#333333",
            scrollbar_button_hover_color="#00ff88"
        )
        self.text_area.pack(expand=True, fill='both', padx=10, pady=(35, 30))
        
        # --- Status Bar ---
        self.status_bar = ctk.CTkFrame(self.main_container, fg_color="#0d0d0d", height=30, corner_radius=10)
        self.status_bar.place(relx=0.5, rely=0.98, anchor='s', relwidth=0.96)
        
        # Modern Dropdown for Language Selection (Expanded)
        self.lang_dropdown = ctk.CTkOptionMenu(
            self.status_bar,
            values=["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Auto", "Interview"],
            width=120,
            height=22,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#1a1a1a",
            button_color="#333333",
            button_hover_color="#00ff88",
            dropdown_fg_color="#1a1a1a",
            dropdown_hover_color="#0066cc",
            text_color="#00ff41", # Phosphor Green default
            command=self._on_lang_change
        )
        self.lang_dropdown.pack(side=tk.LEFT, padx=5)
        self.lang_dropdown.set("Python")
        
        self.meter_bar = ctk.CTkProgressBar(
            self.status_bar, 
            orientation="horizontal", 
            height=6, 
            progress_color="#00ff88",
            fg_color="#1a1a1a"
        )
        self.meter_bar.pack(side=tk.RIGHT, padx=10, expand=True, fill='x')
        self.meter_bar.set(0)

        # Resizing Grip
        self.resize_grip = ctk.CTkLabel(self.main_container, text="◢", text_color="#444444", cursor="sizing")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)

        # Bindings
        self._setup_bindings()
        
        # Apply platform specifics
        self.apply_stealth()

    def _setup_bindings(self):
        # Move bindings - Bind to almost everything to ensure it's movable
        # We also bind to the root itself if possible, but frames are better for ctk
        for widget in [self.main_container, self.status_bar, self.control_frame]:
            widget.bind("<Button-1>", self._start_move)
            widget.bind("<B1-Motion>", self._on_move)
        
        # Also bind a small 'handle' top area
        self.drag_handle = ctk.CTkFrame(self.main_container, fg_color="transparent", height=30)
        self.drag_handle.place(relx=0, rely=0, relwidth=0.7) # Cover top left area
        self.drag_handle.bind("<Button-1>", self._start_move)
        self.drag_handle.bind("<B1-Motion>", self._on_move)
            
        # Resize bindings
        self.resize_grip.bind("<Button-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._on_resize)

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _start_resize(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.start_w = self.root.winfo_width()
        self.start_h = self.root.winfo_height()

    def _on_resize(self, event):
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y
        new_w = max(150, self.start_w + dx)
        new_h = max(100, self.start_h + dy)
        self.root.geometry(f"{new_w}x{new_h}")

    def toggle_notepad(self):
        self.notepad_active = not self.notepad_active
        if self.notepad_active:
             self.notepad_btn.configure(text="🔒", fg_color="#00ff88", text_color="black")
        else:
             self.notepad_btn.configure(text="✎", fg_color="#444444", text_color="white")

    def _on_toggle_click(self):
        if self.on_toggle_mode:
            self.on_toggle_mode()

    def set_mode_icon(self, is_online: bool):
        if is_online:
            self.mode_btn.configure(text="☁️", fg_color="#0066cc")
        else:
            self.mode_btn.configure(text="🏠", fg_color="#333333")

    def show(self, text: str, duration: int = 5):
        self.root.deiconify()
        self.root.lift()
        self.update_text(text, force=True)
        
        if hasattr(self, '_hide_timer') and self._hide_timer:
            self.root.after_cancel(self._hide_timer)
            
        if duration > 0:
            self._hide_timer = self.root.after(duration * 1000, self.root.withdraw)

    def update_text(self, text: str, force: bool = False):
        if self.notepad_active and not force:
             return
        self.text_area.delete("1.0", tk.END)
        self.text_area.configure(text_color=self.active_color)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    def update_caption(self, text: str, is_final: bool = False):
        if self.notepad_active:
             return
        self.text_area.delete("1.0", tk.END)
        if not is_final:
            self.text_area.configure(text_color="#008822") # Dimmer green for partials
        else:
            self.text_area.configure(text_color=self.active_color) # Selected phosphor/custom color
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    def update_meter(self, level: float):
        """level: 0.0 to 1.0"""
        # RMS of 0.2 is very loud, so we boost for visibility
        boosted_level = min(1.0, level * 5.0)
        self.meter_bar.set(boosted_level)
        
        # Dynamic color based on level
        if boosted_level > 0.8:
            self.meter_bar.configure(progress_color="#ff4444")
        elif boosted_level > 0.4:
            self.meter_bar.configure(progress_color="#ffcc00")
        else:
            self.meter_bar.configure(progress_color="#00ff88")

    def set_lock_indicator(self, state_name: str):
        if state_name == "ABSOLUTE_LOCK":
            self.notepad_btn.configure(text="BUNK", fg_color="red", text_color="white")
            self.root.attributes("-alpha", 1.0)
        elif state_name == "NORMAL_LOCK":
            self.notepad_btn.configure(text="LOCK", fg_color="orange", text_color="black")
            self.root.attributes("-alpha", 0.95)
        else:
            self.notepad_btn.configure(text="✎", fg_color="#444444", text_color="white")
            self.root.attributes("-alpha", 1.0)

    def set_language_indicator(self, lang: str):
        self.lang_dropdown.set(lang)
        if lang.upper() == "PYTHON":
            self.lang_dropdown.configure(text_color="#00ff88")
        else:
            self.lang_dropdown.configure(text_color="#00ccff")

    def _on_lang_change(self, selected_lang: str):
        """Callback for dropdown selection."""
        if hasattr(self, 'on_lang_change_callback') and self.on_lang_change_callback:
            self.on_lang_change_callback(selected_lang)

    def set_lang_callback(self, callback: Callable[[str], None]):
        """Sets the callback for when the language is changed via dropdown."""
        self.on_lang_change_callback = callback

    def _on_color_change(self, color_name: str):
        """Callback for color dropdown selection."""
        color_map = {
            "Green": "#00ff41",
            "Blue": "#00ccff",
            "Orange": "#ffcc00",
            "Red": "#ff4444",
            "White": "#ffffff"
        }
        self.active_color = color_map.get(color_name, "#00ff41")
        self.text_area.configure(text_color=self.active_color)
        self.lang_dropdown.configure(text_color=self.active_color)
        self.color_dropdown.configure(text_color=self.active_color)
        # Update without closing
        self.update_text(self.text_area.get("1.0", tk.END), force=True)

    def apply_stealth(self):
        self.root.update()
        system = platform.system()
        if system == "Windows":
            try:
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                # WDA_EXCLUDEFROMCAPTURE = 0x11
                user32.SetWindowDisplayAffinity(hwnd, 0x11)
                logger.info("Stealth applied (Windows)")
            except:
                pass
        
    def close(self):
        self.root.destroy()

def test_modern_overlay():
    root = tk.Tk()
    overlay = StealthOverlayModern(root)
    # Test text: "reverse string py"
    content = """// MODERN UI TEST: reverse string py
    
def reverse_string(s):
    return s[::-1]

print(reverse_string("hello")) # Output: olleh
"""
    overlay.update_caption(content, is_final=True)
    overlay.update_meter(0.15)
    root.mainloop()

if __name__ == "__main__":
    test_modern_overlay()
