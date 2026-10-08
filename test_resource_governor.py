import os
import sys
import time
import pytest
from unittest.mock import Mock, patch

from resource_governor import (
    set_low_process_priority,
    get_safe_worker_threads,
    get_available_memory_mb,
    is_memory_safe,
    TokenBatcher,
    ResourceGovernor,
)


class TestResourceGovernorFunctions:
    """Tests for low-level resource management functions."""

    def test_safe_worker_threads(self):
        """Test calculation of safe worker threads leaving cores for UI."""
        with patch("os.cpu_count", return_value=8):
            threads = get_safe_worker_threads(reserved_cores=2)
            assert threads == 6

        with patch("os.cpu_count", return_value=2):
            threads = get_safe_worker_threads(reserved_cores=2)
            assert threads == 1  # Never drops below 1

        with patch("os.cpu_count", return_value=1):
            threads = get_safe_worker_threads(reserved_cores=2)
            assert threads == 1

    def test_memory_headroom_safe(self):
        """Test is_memory_safe when RAM is sufficient."""
        with patch("resource_governor.get_available_memory_mb", return_value=8192.0):
            is_safe, avail = is_memory_safe(min_headroom_mb=1024)
            assert is_safe is True
            assert avail == 8192.0

    def test_memory_headroom_low(self):
        """Test is_memory_safe when RAM is below minimum safe threshold."""
        with patch("resource_governor.get_available_memory_mb", return_value=512.0):
            is_safe, avail = is_memory_safe(min_headroom_mb=1024)
            assert is_safe is False
            assert avail == 512.0

    def test_set_low_process_priority_psutil(self):
        """Test set_low_process_priority when psutil is available."""
        mock_p = Mock()
        with patch.dict("sys.modules", {"psutil": Mock(Process=Mock(return_value=mock_p), BELOW_NORMAL_PRIORITY_CLASS=0x4000)}):
            result = set_low_process_priority("below_normal")
            assert result is True


class TestTokenBatcher:
    """Tests for TokenBatcher to ensure smooth UI queue processing."""

    def test_token_batcher_char_threshold(self):
        """Test that batcher flushes when accumulated length reaches max_chars."""
        batcher = TokenBatcher(max_interval_sec=1.0, max_chars=10)
        # Add 4 chars
        assert batcher.add("1234") is None
        # Add 6 more chars -> total 10 -> should flush
        flushed = batcher.add("567890")
        assert flushed == "1234567890"

    def test_token_batcher_interval_threshold(self):
        """Test that batcher flushes after max_interval_sec elapses."""
        batcher = TokenBatcher(max_interval_sec=0.01, max_chars=100)
        assert batcher.add("token1") is None
        time.sleep(0.02)
        flushed = batcher.add("token2")
        assert flushed == "token1token2"

    def test_token_batcher_flush(self):
        """Test manual flush of remaining tokens."""
        batcher = TokenBatcher(max_interval_sec=10.0, max_chars=100)
        batcher.add("hello")
        batcher.add(" ")
        batcher.add("world")
        assert batcher.flush() == "hello world"
        assert batcher.flush() == ""  # Empty after flush


class TestResourceGovernorClass:
    """Tests for the ResourceGovernor coordinator class."""

    @patch.dict("os.environ", {"RESOURCE_GOVERNOR_ENABLED": "true", "RESERVED_CPU_CORES": "3"})
    def test_governor_init_and_threads(self):
        gov = ResourceGovernor()
        assert gov.enabled is True
        assert gov.reserved_cores == 3
        with patch("os.cpu_count", return_value=8):
            assert gov.get_thread_count() == 5

    @patch.dict("os.environ", {"RESOURCE_GOVERNOR_ENABLED": "false"})
    def test_governor_disabled(self):
        gov = ResourceGovernor()
        assert gov.enabled is False
        assert gov.apply_protection() is False
        with patch("os.cpu_count", return_value=8):
            assert gov.get_thread_count() == 8

    def test_governor_check_memory(self):
        gov = ResourceGovernor()
        with patch("resource_governor.get_available_memory_mb", return_value=4096.0):
            safe, avail = gov.check_memory()
            assert safe is True
            assert avail == 4096.0

    def test_governor_create_batcher(self):
        gov = ResourceGovernor()
        batcher = gov.create_batcher()
        assert isinstance(batcher, TokenBatcher)
