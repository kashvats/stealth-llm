import tkinter as tk
import platform
import ctypes
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class StealthOverlay:
    def __init__(self, root: tk.Tk, on_toggle_mode=None):
        self.root = root
        self.notepad_active = False
        self.on_toggle_mode = on_toggle_mode
        self.root.title("Stealth Pilot")
        self.root.geometry("400x200+10+10")
        self.root.overrideredirect(True) # Remove title bar
        self.root.attributes("-topmost", True) # Always on top
        self.root.attributes("-alpha", 0.8) # Slight transparency
        
        self.x = 0
        self.y = 0
        
        self.notepad_active = False
        
        self.text_area = tk.Text(self.root, bg="black", fg="white", font=("Arial", 12), wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')
        
        # Control Frame (Overlay Buttons)
        self.control_frame = tk.Frame(self.root, bg="black")
        self.control_frame.place(relx=1.0, rely=0.0, anchor='ne')
        
        # Close Button
        self.close_button = tk.Button(self.control_frame, text="X", command=self.close, bg="red", fg="white", font=("Arial", 8), width=3)
        self.close_button.pack(side=tk.RIGHT, padx=2)
        
        # Drag bindings
        self.root.bind("<Button-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._on_move)
        self.text_area.bind("<Button-1>", self._start_move)
        self.text_area.bind("<B1-Motion>", self._on_move)
        self.control_frame.bind("<Button-1>", self._start_move) # Allow dragging from control frame
        self.control_frame.bind("<B1-Motion>", self._on_move)
        
        # Buttons
        self.notepad_btn = tk.Button(
            self.control_frame, text="✎", font=("Arial", 10),
            bg="gray", fg="white", command=self.toggle_notepad,
            width=3
        )
        self.notepad_btn.pack(side=tk.RIGHT, padx=2)

        # Toggle Mode Button (Cloud vs Local)
        self.toggle_mode_btn = tk.Button(
            self.control_frame, text="🏠", font=("Arial", 10),
            bg="#444444", fg="white", command=self._on_toggle_click,
            width=3
        )
        self.toggle_mode_btn.pack(side=tk.RIGHT, padx=2)
        
        self.resize_grip = tk.Label(self.root, text="◢", bg="black", fg="gray", cursor="sizing")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor='se')
        self.resize_grip.bind("<Button-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._on_resize)

        # Language Indicator (Bottom Left)
        self.lang_label = tk.Label(self.root, text="PY", bg="black", fg="#00ff00", font=("Arial", 8, "bold"))
        self.lang_label.place(relx=0.0, rely=1.0, anchor='sw')
        
        # Volume Meter (Bottom Center)
        self.meter_frame = tk.Frame(self.root, bg="#222222", height=4)
        self.meter_frame.place(relx=0.5, rely=1.0, anchor='s', relwidth=0.6)
        self.meter_bar = tk.Frame(self.meter_frame, bg="#00ff00", width=0, height=4)
        self.meter_bar.place(x=0, y=0)

        # Language Indicator (Bottom Left)
        self.lang_label = tk.Label(self.root, text="PY", bg="black", fg="#00ff00", font=("Arial", 8, "bold"))
        self.lang_label.place(relx=0.0, rely=1.0, anchor='sw')
        
        self.apply_stealth()

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
        new_w = max(100, self.start_w + dx)
        new_h = max(50, self.start_h + dy)
        self.root.geometry(f"{new_w}x{new_h}")

    def toggle_notepad(self):
        self.notepad_active = not self.notepad_active
        if self.notepad_active:
             self.notepad_btn.config(text="🔒", bg="green")
        else:
             self.notepad_btn.config(text="✎", bg="gray")

    def _on_toggle_click(self):
        if self.on_toggle_mode:
            self.on_toggle_mode()

    def set_mode_icon(self, is_online: bool):
        if is_online:
            self.toggle_mode_btn.config(text="☁️", bg="#0066cc") # Blue for Cloud
        else:
            self.toggle_mode_btn.config(text="🏠", bg="#444444") # Dark for Local

    def show(self, text: str, duration: int = 5):
        """Displays text on the overlay for a set duration."""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)
        self.root.deiconify()
        self.root.lift()
        
        # Cancel previous timer if exists
        if hasattr(self, '_hide_timer') and self._hide_timer:
            self.root.after_cancel(self._hide_timer)
            
        if duration > 0:
            self._hide_timer = self.root.after(duration * 1000, self.root.withdraw)

    def apply_stealth(self):
        self.root.update() # CRITICAL: Ensure window is realized before getting HWND
        
        system = platform.system()
        if system == "Windows":
            try:
                user32 = ctypes.windll.user32
                
                # Logic from llm_offline reference
                hwnd = user32.GetParent(self.root.winfo_id())
                if not hwnd:
                    hwnd = self.root.winfo_id()
                
                # Constants
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                WDA_MONITOR = 0x00000001
                
                # Try EXCLUDEFROMCAPTURE
                result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
                
                if result:
                     logger.info(f"Success: Stealth Mode (EXCLUDEFROMCAPTURE) applied to HWND {hwnd}")
                else:
                     logger.warning(f"Failed EXCLUDEFROMCAPTURE. Trying WDA_MONITOR...")
                     result = user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
                     if result:
                         logger.info(f"Success: Stealth Mode (MONITOR) applied to HWND {hwnd}")
                     else:
                         logger.error("Failed Stealth Mode completely.")

            except Exception as e:
                logger.error(f"Failed to apply Windows stealth: {e}")
        elif system == "Darwin":
            logger.info("MacOS Stealth: Recommend sharing specific window instead of screen.")
        elif system == "Linux":
            logger.info("Linux Stealth: Recommend sharing specific window instead of screen.")

    def set_lock_indicator(self, state_name: str):
        """Updates the lock indicator visual."""
        if state_name == "ABSOLUTE_LOCK":
            self.notepad_btn.config(text="BUNKER", bg="red", fg="white")
            self.root.attributes("-alpha", 1.0) # Full opacity in bunker
        elif state_name == "NORMAL_LOCK":
            self.notepad_btn.config(text="LOCKED", bg="orange", fg="black")
            self.root.attributes("-alpha", 0.9)
        else:
            self.notepad_btn.config(text="✎", bg="gray", fg="white")
            self.root.attributes("-alpha", 0.8)

    def set_language_indicator(self, lang: str):
        """Updates the language label."""
        if lang.upper() == "PYTHON":
            self.lang_label.config(text="PY", fg="#00ff00")
        else:
            self.lang_label.config(text="AUTO", fg="#00ccff")

    def update_meter(self, level: float):
        """level: 0.0 to 1.0"""
        base_width = self.meter_frame.winfo_width()
        if base_width <= 1: base_width = 240 # Fallback for uninitialized window
        width = int(level * 5.0 * base_width) # Boost level for visibility (RMS 0.2 is very loud)
        width = min(width, base_width)
        self.meter_bar.place_configure(width=width)
        # Change color based on level
        if level > 0.8: color = "red"
        elif level > 0.4: color = "yellow"
        else: color = "#00ff00"
        self.meter_bar.config(bg=color)

    def set_language_indicator(self, lang: str):
        """Updates the language label."""
        if lang.upper() == "PYTHON":
            self.lang_label.config(text="PY", fg="#00ff00")
        else:
            self.lang_label.config(text="AUTO", fg="#00ccff")

    def update_text(self, text: str, force: bool = False):
        if self.notepad_active and not force:
             return
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.root.update_idletasks()

    def update_caption(self, text: str, is_final: bool = False):
        if self.notepad_active:
             return
        
        self.text_area.delete(1.0, tk.END)
        
        # Simulating a "history" + "current" view could be complex
        # For now, just show the current text. 
        # If is_final, maybe prefix?
        # The user request: "Final sentences must replace earlier temporary text... Each finalized sentence is sent to LLM".
        # So we probably want to show the stream.
        
        # Let's keep it simple: Just show the text. 
        # We might need a separate mechanism if we want to show a history of captions.
        # But per request "display text immediately... replace earlier temporary", it implies a single active display or a stream.
        
        # Visual distinction
        if not is_final:
            self.text_area.config(fg="#aaaaaa", font=("Arial", 12, "italic"))
        else:
            self.text_area.config(fg="white", font=("Arial", 12, "normal"))
            
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.root.update_idletasks()

    def close(self):
        self.root.destroy()

def run_overlay():
    root = tk.Tk()
    app = StealthOverlay(root)
    root.mainloop()

if __name__ == "__main__":
    run_overlay()
