import threading
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class LockState(Enum):
    UNLOCKED = auto()
    NORMAL_LOCK = auto()
    ABSOLUTE_LOCK = auto()

class LockManager:
    """Manages the interrupt-lock system for the Silent Strategist."""
    
    def __init__(self, on_state_change=None):
        self.state = LockState.UNLOCKED
        self.on_state_change = on_state_change
        self._lock = threading.RLock()

    def set_state(self, new_state: LockState):
        with self._lock:
            if self.state != new_state:
                logger.info(f"LockManager: Changing state from {self.state.name} to {new_state.name}")
                self.state = new_state
                if self.on_state_change:
                    self.on_state_change(self.state)

    def get_state(self) -> LockState:
        with self._lock:
            return self.state

    def is_locked(self) -> bool:
        with self._lock:
            return self.state != LockState.UNLOCKED

    def is_absolute(self) -> bool:
        with self._lock:
            return self.state == LockState.ABSOLUTE_LOCK

    def try_unlock(self, force: bool = False):
        """
        Attempts to unlock the system.
        Normal locks can be unlocked via auto-completion.
        Absolute locks require manual override (force=True).
        """
        with self._lock:
            if self.state == LockState.NORMAL_LOCK:
                self.set_state(LockState.UNLOCKED)
            elif self.state == LockState.ABSOLUTE_LOCK and force:
                self.set_state(LockState.UNLOCKED)
            elif self.state == LockState.ABSOLUTE_LOCK:
                logger.info("LockManager: Manual unlock required for Absolute Lock.")

    def toggle_absolute(self):
        with self._lock:
            if self.state == LockState.ABSOLUTE_LOCK:
                self.set_state(LockState.UNLOCKED)
            else:
                self.set_state(LockState.ABSOLUTE_LOCK)
