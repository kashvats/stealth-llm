import pytest
from lock_manager import LockManager, LockState

def test_initial_state():
    lm = LockManager()
    assert lm.state == LockState.UNLOCKED
    assert not lm.is_locked()

def test_normal_lock():
    lm = LockManager()
    lm.set_state(LockState.NORMAL_LOCK)
    assert lm.is_locked()
    assert not lm.is_absolute()
    
    lm.try_unlock()
    assert not lm.is_locked()

def test_absolute_lock():
    lm = LockManager()
    lm.set_state(LockState.ABSOLUTE_LOCK)
    assert lm.is_locked()
    assert lm.is_absolute()
    
    # Auto-unlock attempt should fail
    lm.try_unlock(force=False)
    assert lm.state == LockState.ABSOLUTE_LOCK
    
    # Manual unlock should succeed
    lm.try_unlock(force=True)
    assert lm.state == LockState.UNLOCKED

def test_toggle_absolute():
    lm = LockManager()
    lm.toggle_absolute()
    assert lm.state == LockState.ABSOLUTE_LOCK
    lm.toggle_absolute()
    assert lm.state == LockState.UNLOCKED

def test_callback():
    callback_called = False
    def on_change(state):
        nonlocal callback_called
        callback_called = True
        
    lm = LockManager(on_state_change=on_change)
    lm.set_state(LockState.NORMAL_LOCK)
    assert callback_called
