import os
import sys
import time
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Windows Priority Constants
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
IDLE_PRIORITY_CLASS = 0x00000040
NORMAL_PRIORITY_CLASS = 0x00000020


def set_low_process_priority(priority_level: str = "below_normal") -> bool:
    """
    Sets the current process priority to lower than normal so that heavy
    inference or model operations do not freeze the desktop UI, mouse, or screen.
    Uses native Windows APIs or POSIX os.nice with zero mandatory dependencies.
    """
    try:
        # Check psutil if present
        try:
            import psutil
            p = psutil.Process()
            if sys.platform == "win32":
                val = psutil.BELOW_NORMAL_PRIORITY_CLASS if priority_level == "below_normal" else psutil.IDLE_PRIORITY_CLASS
                p.nice(val)
            else:
                p.nice(10)
            logger.info(f"Process priority set via psutil ({priority_level}).")
            return True
        except ImportError:
            pass

        # Native Windows implementation via ctypes
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel32.SetPriorityClass.restype = wintypes.BOOL

            flag = BELOW_NORMAL_PRIORITY_CLASS if priority_level == "below_normal" else IDLE_PRIORITY_CLASS
            handle = kernel32.GetCurrentProcess()
            res = kernel32.SetPriorityClass(handle, flag)
            if res:
                logger.info(f"Windows process priority set to {priority_level} (0x{flag:X}).")
                return True
            else:
                err = ctypes.get_last_error()
                logger.warning(f"Failed to set Windows process priority (error code {err}).")
                return False
        else:
            # POSIX implementation
            if hasattr(os, "nice"):
                increment = 10 if priority_level == "below_normal" else 15
                os.nice(increment)
                logger.info(f"POSIX process nice adjusted by +{increment}.")
                return True
    except Exception as e:
        logger.warning(f"Failed to lower process priority: {e}")
    return False


def get_safe_worker_threads(reserved_cores: int = 2) -> int:
    """
    Calculates a safe number of worker threads so that at least reserved_cores
    remain free for the OS, screen rendering, and UI event loops.
    """
    total = os.cpu_count() or 4
    return max(1, total - max(0, reserved_cores))


def get_available_memory_mb() -> float:
    """
    Returns available physical system memory in megabytes without requiring psutil.
    """
    # 1. Check psutil
    try:
        import psutil
        return psutil.virtual_memory().available / (1024.0 * 1024.0)
    except ImportError:
        pass

    # 2. Windows via GlobalMemoryStatusEx
    if sys.platform == "win32":
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32 = ctypes.windll.kernel32
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return stat.ullAvailPhys / (1024.0 * 1024.0)
        except Exception as e:
            logger.debug(f"GlobalMemoryStatusEx failed: {e}")

    # 3. Linux /proc/meminfo
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        kb = float(line.split()[1])
                        return kb / 1024.0
        except Exception as e:
            logger.debug(f"Reading /proc/meminfo failed: {e}")

    # Fallback default: assume 4096 MB if cannot inspect
    return 4096.0


def is_memory_safe(min_headroom_mb: int = 1024) -> Tuple[bool, float]:
    """
    Returns (is_safe, available_mb). If available_mb < min_headroom_mb,
    running a heavy model may trigger swap/paging thrashing that freezes the OS.
    """
    avail = get_available_memory_mb()
    return (avail >= min_headroom_mb, avail)


class TokenBatcher:
    """
    Batches rapid stream tokens across a short time interval or character limit
    to prevent UI queue floods and keep Tkinter render loops at 60 FPS.
    """
    def __init__(self, max_interval_sec: float = 0.03, max_chars: int = 15):
        self.max_interval_sec = max_interval_sec
        self.max_chars = max_chars
        self._buffer = []
        self._last_flush = time.time()

    def add(self, token: str) -> Optional[str]:
        """
        Adds a token. If the buffer is ready to be flushed, returns the batched string.
        Otherwise returns None.
        """
        self._buffer.append(token)
        now = time.time()
        curr_len = sum(len(t) for t in self._buffer)
        if (now - self._last_flush >= self.max_interval_sec) or (curr_len >= self.max_chars):
            return self.flush()
        return None

    def flush(self) -> str:
        """Flushes and returns all accumulated tokens."""
        if not self._buffer:
            return ""
        batch = "".join(self._buffer)
        self._buffer = []
        self._last_flush = time.time()
        return batch


class ResourceGovernor:
    """
    Coordinates process priority tuning, core reservation, memory safety,
    and token batching for smooth model execution.
    """
    def __init__(self):
        self.enabled = os.getenv("RESOURCE_GOVERNOR_ENABLED", "true").lower() in ("true", "1", "yes")
        self.low_priority = os.getenv("LOW_PRIORITY_INFERENCE", "true").lower() in ("true", "1", "yes")
        try:
            self.reserved_cores = int(os.getenv("RESERVED_CPU_CORES", "2"))
        except (ValueError, TypeError):
            self.reserved_cores = 2
        try:
            self.min_free_ram_mb = int(os.getenv("MIN_FREE_RAM_MB", "1024"))
        except (ValueError, TypeError):
            self.min_free_ram_mb = 1024

    def apply_protection(self) -> bool:
        """Applies process priority reduction if enabled."""
        if not self.enabled or not self.low_priority:
            return False
        return set_low_process_priority("below_normal")

    def get_thread_count(self) -> int:
        """Gets safe number of worker threads to avoid core saturation."""
        if not self.enabled:
            return os.cpu_count() or 4
        return get_safe_worker_threads(self.reserved_cores)

    def check_memory(self) -> Tuple[bool, float]:
        """Checks if there is enough physical RAM to execute safely."""
        if not self.enabled:
            return True, get_available_memory_mb()
        return is_memory_safe(self.min_free_ram_mb)

    def create_batcher(self) -> TokenBatcher:
        """Creates a TokenBatcher tuned for the environment."""
        return TokenBatcher(max_interval_sec=0.03, max_chars=15)
