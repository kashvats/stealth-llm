from pynput import keyboard
import logging

logger = logging.getLogger(__name__)

class GlobalHotkeyListener:
    def __init__(self, callbacks):
        """
        callbacks: dict mapping hotkey names to functions.
        Example: {'toggle_listen': fn, 'close': fn, ...}
        """
        self.callbacks = callbacks
        self.listener = None
        
        # Hotkeys are Alt+Shift+<key>
        self.hotkeys = {
            '<alt>+<shift>+z': self.callbacks.get('toggle_listen'),
            '<alt>+<shift>+x': self.callbacks.get('close'),
            '<alt>+<shift>+v': self.callbacks.get('copy_paste'),
            '<alt>+<shift>+d': self.callbacks.get('dsa_mode'),
            '<alt>+<shift>+k': self.callbacks.get('absolute_lock'),
            '<alt>+<shift>+l': self.callbacks.get('unlock'),
            '<alt>+<shift>+p': self.callbacks.get('toggle_language'),
            '<alt>+<shift>+c': self.callbacks.get('toggle_clipboard'),
            '<alt>+<shift>+r': self.callbacks.get('rescan_audio'),
            '<ctrl>+<shift>+<esc>+<esc>': self.callbacks.get('emergency_stop') 
        }

    def start(self):
        # We'll use GlobalHotKeys for convenience
        # Note: double ESC is tricky with pynput, we might just handle double press logic elsewhere 
        # but let's try to bind it or use a simplified combo.
        
        def on_activate_z(): self.callbacks.get('toggle_listen')()
        def on_activate_x(): self.callbacks.get('close')()
        def on_activate_v(): self.callbacks.get('copy_paste')()
        def on_activate_d(): self.callbacks.get('dsa_mode')()
        def on_activate_k(): self.callbacks.get('absolute_lock')()
        def on_activate_l(): self.callbacks.get('unlock')()
        def on_activate_esc(): self._handle_esc()

        self.esc_count = 0
        self.last_esc_time = 0

        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+z': self.callbacks.get('toggle_listen'),
            '<ctrl>+<shift>+x': self.callbacks.get('close'),
            '<ctrl>+<shift>+v': self.callbacks.get('copy_paste'),
            '<ctrl>+<shift>+d': self.callbacks.get('dsa_mode'),
            '<ctrl>+<shift>+k': self.callbacks.get('absolute_lock'),
            '<ctrl>+<shift>+l': self.callbacks.get('unlock'),
            '<ctrl>+<shift>+p': self.callbacks.get('toggle_language'),
            '<ctrl>+<shift>+c': self.callbacks.get('toggle_clipboard'),
            '<ctrl>+<shift>+r': self.callbacks.get('rescan_audio')
        })
        
        # For double ESC, we might need a regular listener to catch it
        self.esc_listener = keyboard.Listener(on_press=self._on_press)
        
        self.listener.start()
        self.esc_listener.start()
        logger.info("Global Hotkey Listener started.")

    def _on_press(self, key):
        if key == keyboard.Key.esc:
            import time
            now = time.time()
            if now - self.last_esc_time < 0.5:
                self.esc_count += 1
            else:
                self.esc_count = 1
            self.last_esc_time = now
            
            if self.esc_count >= 2:
                logger.warning("EMERGENCY STOP TRIGGERED.")
                self.callbacks.get('emergency_stop')()

    def stop(self):
        if self.listener:
            self.listener.stop()
        if self.esc_listener:
            self.esc_listener.stop()
