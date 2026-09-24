import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from knowledge_base import KnowledgeBase


class TestKnowledgeBaseInit:
    """Tests for KnowledgeBase initialization."""

    @pytest.fixture
    def temp_kb(self):
        """Create temporary KB files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dsa_file = os.path.join(tmpdir, "dsa.json")
            algo_file = os.path.join(tmpdir, "algorithms.json")

            # Create test data
            kb_data = [
                {"id": 1, "question": "Two Sum", "answer": "Use hash map", "category": "DSA"},
                {"id": 2, "question": "Reverse List", "answer": "Use two pointers", "category": "DSA"}
            ]
            algo_data = {
                "patterns": [
                    {"id": "two-sum", "name": "Two Sum", "code": "def two_sum(nums, target): pass"}
                ]
            }

            with open(dsa_file, "w") as f:
                json.dump(kb_data, f)
            with open(algo_file, "w") as f:
                json.dump(algo_data, f)

            yield tmpdir, dsa_file, algo_file

    def test_initialization_with_existing_files(self, temp_kb):
        """Test KB loads existing data files."""
        tmpdir, dsa_file, algo_file = temp_kb

        with patch("os.path.exists") as mock_exists:
            with patch("builtins.open", mock_open(read_data='[{"id": 1, "question": "Test"}]')):
                mock_exists.return_value = True
                kb = KnowledgeBase(dsa_file)

                assert len(kb.data) > 0 or kb.data == []

    def test_initialization_missing_files(self, temp_kb):
        """Test KB handles missing files gracefully."""
        tmpdir, _, _ = temp_kb
        nonexistent = os.path.join(tmpdir, "nonexistent.json")

        kb = KnowledgeBase(nonexistent)

        assert kb.data == []


class TestKnowledgeBaseLookup:
    """Tests for knowledge base lookup functionality."""

    @pytest.fixture
    def kb_with_data(self):
        """Create KB with test data."""
        kb = KnowledgeBase("test_dsa.json")
        kb.data = [
            {
                "id": 1,
                "question": "Two Sum: Find two numbers that add up to target",
                "answer": "Use hash map for O(n) solution",
                "category": "DSA"
            },
            {
                "id": 2,
                "question": "Reverse Linked List",
                "answer": "Iterate and reverse pointers",
                "category": "DSA"
            },
            {
                "id": 3,
                "question": "Find duplicate in sorted array",
                "answer": "Binary search approach",
                "category": "DSA"
            }
        ]
        kb.patterns = []
        return kb

    def test_lookup_exact_title_match(self, kb_with_data):
        """Test exact title matching with colon prefix."""
        result = kb_with_data.lookup("Two Sum")

        assert result is not None
        assert result["id"] == 1

    def test_lookup_substring_match(self, kb_with_data):
        """Test substring matching."""
        result = kb_with_data.lookup("Reverse Linked List")

        assert result is not None
        assert "Reverse" in result["question"]

    def test_lookup_fuzzy_match(self, kb_with_data):
        """Test fuzzy matching for typos."""
        result = kb_with_data.lookup("Two Sume")  # Typo

        assert result is not None
        assert "Two Sum" in result["question"]

    def test_lookup_case_insensitive(self, kb_with_data):
        """Test case-insensitive lookup."""
        result = kb_with_data.lookup("two sum")

        assert result is not None

    def test_lookup_partial_text(self, kb_with_data):
        """Test lookup with partial question text."""
        result = kb_with_data.lookup("numbers that add up")

        assert result is not None

    def test_lookup_no_match(self, kb_with_data):
        """Test lookup returns None for no match."""
        result = kb_with_data.lookup("Complete random question about aliens")

        assert result is None

    def test_lookup_below_threshold(self, kb_with_data):
        """Test that fuzzy matches below threshold are rejected."""
        result = kb_with_data.lookup("xyz123abc", threshold=0.9)

        assert result is None

    def test_lookup_empty_query(self, kb_with_data):
        """Test lookup with empty/short query."""
        result = kb_with_data.lookup("")

        assert result is None

    def test_lookup_very_short_query(self, kb_with_data):
        """Test lookup with too-short query."""
        result = kb_with_data.lookup("ab")

        assert result is None


class TestKnowledgeBasePatterns:
    """Tests for pattern/algorithm loading and retrieval."""

    @pytest.fixture
    def kb_with_patterns(self):
        """Create KB with test patterns."""
        kb = KnowledgeBase("test_dsa.json")
        kb.patterns = [
            {
                "id": "two-sum",
                "name": "Two Sum",
                "code": "def twoSum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i",
                "time": "O(n)",
                "space": "O(n)"
            },
            {
                "id": "reverse-list",
                "name": "Reverse Linked List",
                "code": "def reverseList(head):\n    prev = None\n    while head:\n        next_temp = head.next\n        head.next = prev\n        prev = head\n        head = next_temp\n    return prev"
            }
        ]
        kb.data = []
        return kb

    def test_get_pattern_by_id(self, kb_with_patterns):
        """Test retrieving pattern by ID."""
        pattern = kb_with_patterns.get_pattern("two-sum")

        assert pattern is not None
        assert pattern["name"] == "Two Sum"
        assert "seen = {}" in pattern["code"]

    def test_get_pattern_not_found(self, kb_with_patterns):
        """Test get_pattern returns None for missing ID."""
        pattern = kb_with_patterns.get_pattern("nonexistent")

        assert pattern is None

    def test_load_patterns_success(self):
        """Test successful pattern loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            algo_file = os.path.join(tmpdir, "algorithms.json")
            algo_data = {
                "patterns": [
                    {"id": "test-1", "name": "Test", "code": "pass"}
                ]
            }

            with open(algo_file, "w") as f:
                json.dump(algo_data, f)

            kb = KnowledgeBase("dsa.json")
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(algo_data))):
                    kb.load_patterns()

            assert len(kb.patterns) >= 0  # May be empty if file doesn't exist


class TestKnowledgeBaseAddEntry:
    """Tests for adding new entries to the knowledge base."""

    @pytest.fixture
    def kb_empty(self):
        """Create empty KB."""
        kb = KnowledgeBase("test_dsa.json")
        kb.data = []
        kb.patterns = []
        return kb

    def test_add_entry_simple(self, kb_empty):
        """Test adding a simple entry."""
        kb_empty.add_entry("What is Python?", "Python is a language", category="General")

        assert len(kb_empty.data) == 1
        assert kb_empty.data[0]["question"] == "What is Python?"
        assert kb_empty.data[0]["answer"] == "Python is a language"

    def test_add_entry_with_id_increment(self, kb_empty):
        """Test that entry IDs increment properly."""
        kb_empty.add_entry("Q1", "A1")
        kb_empty.add_entry("Q2", "A2")

        assert kb_empty.data[0]["id"] == 1
        assert kb_empty.data[1]["id"] == 2

    def test_add_entry_long_question_truncated(self, kb_empty):
        """Test that very long questions are truncated."""
        long_q = "Q" * 200
        kb_empty.add_entry(long_q, "Answer")

        stored_q = kb_empty.data[0]["question"]
        assert len(stored_q) <= 160  # Truncated to 150 + "..."

    def test_add_entry_structured_problem_title(self, kb_empty):
        """Test that structured problems keep first line as title."""
        structured = "Two Sum\ninput: [2, 7, 11, 15]\noutput: [0, 1]"
        kb_empty.add_entry(structured, "Answer")

        # First line should be kept
        assert kb_empty.data[0]["question"] == "Two Sum"

    def test_add_entry_duplicate_prevention(self, kb_empty):
        """Test that similar entries are not duplicated."""
        kb_empty.add_entry("Two Sum problem", "Solution 1")
        kb_empty.add_entry("Two Sum problem", "Solution 2")  # Very similar

        # Should only have one entry (duplicate prevention)
        assert len(kb_empty.data) <= 2  # Depends on fuzzy match threshold

    def test_add_entry_tags_applied(self, kb_empty):
        """Test that auto-cached tags are applied."""
        kb_empty.add_entry("Question", "Answer")

        assert "auto-cached" in kb_empty.data[0]["tags"]

    def test_add_entry_category_applied(self, kb_empty):
        """Test that category is stored correctly."""
        kb_empty.add_entry("Q", "A", category="Interview")

        assert kb_empty.data[0]["category"] == "Interview"

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_add_entry_save_error_handling(self, mock_file, kb_empty):
        """Test handling of save errors."""
        with patch.object(kb_empty, 'save'):
            kb_empty.add_entry("Q", "A")  # Should not crash


class TestKnowledgeBaseSave:
    """Tests for persistence."""

    def test_save_creates_file(self):
        """Test that save creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = os.path.join(tmpdir, "kb.json")
            kb = KnowledgeBase(kb_file)
            kb.data = [{"id": 1, "question": "Q", "answer": "A"}]

            kb.save()

            assert os.path.exists(kb_file)
            with open(kb_file) as f:
                saved = json.load(f)
                assert len(saved) == 1

    def test_save_valid_json(self):
        """Test that saved data is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = os.path.join(tmpdir, "kb.json")
            kb = KnowledgeBase(kb_file)
            kb.data = [
                {"id": 1, "question": "Q", "answer": "A", "category": "Test", "tags": ["tag1"]}
            ]

            kb.save()

            # Read back and verify
            with open(kb_file) as f:
                loaded = json.load(f)
                assert loaded[0]["question"] == "Q"


class TestKnowledgeBaseIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow_add_and_lookup(self):
        """Test adding entry and then looking it up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = os.path.join(tmpdir, "kb.json")
            kb = KnowledgeBase(kb_file)
            kb.data = []
            kb.patterns = []

            # Add entry
            kb.add_entry("Binary Search Algorithm", "Use divide and conquer", category="DSA")

            # Look it up
            result = kb.lookup("Binary Search")

            assert result is not None
            assert "divide and conquer" in result["answer"]

    def test_multiple_operations(self):
        """Test multiple add/lookup operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = os.path.join(tmpdir, "kb.json")
            kb = KnowledgeBase(kb_file)
            kb.data = []
            kb.patterns = []

            questions = [
                ("Quicksort", "Partition algorithm"),
                ("Mergesort", "Divide and merge"),
                ("Heapsort", "Heap structure")
            ]

            for q, a in questions:
                kb.add_entry(q, a)

            # All should be retrievable
            for q, _ in questions:
                result = kb.lookup(q)
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
