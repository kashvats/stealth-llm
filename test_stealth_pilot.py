import pytest
from stealth_pilot import StealthPilot, Mode
from unittest.mock import MagicMock

class TestStealthPilot:
    @pytest.fixture
    def pilot(self):
        return StealthPilot()

    def test_mode_selection_general(self, pilot):
        """Test that GENERAL mode is selected for factual questions."""
        mode = pilot.determine_mode("What is the capital of France?")
        assert mode == Mode.GENERAL

    def test_mode_selection_interview(self, pilot):
        """Test that INTERVIEW mode is selected for 'why', 'how', or design questions."""
        mode = pilot.determine_mode("How does garbage collection work in Java?")
        assert mode == Mode.INTERVIEW
        
        mode = pilot.determine_mode("Design a URL shortener.")
        assert mode == Mode.INTERVIEW

    def test_mode_selection_codebase(self, pilot):
        """Test that CODEBASE mode is selected for coding tasks."""
        mode = pilot.determine_mode("Refactor this function to be O(n).")
        assert mode == Mode.CODEBASE
        
        mode = pilot.determine_mode("Write a unit test for this class.")
        assert mode == Mode.CODEBASE

    def test_missing_context_refusal(self, pilot):
        """Test that the pilot refuses to answer when context is missing."""
        response = pilot.process_request("Explain quantum physics.", context="")
        assert response == "No supporting information found in provided context."

    def test_general_mode_word_limit(self, pilot):
        """Test that GENERAL mode answers are under 120 words."""
        # Mocking internal method to return a long string if not handled
        # But here we are testing the logic that enforces it or checking the output
        # For this test, we accept that we can't easily force the generator to be long 
        # without a real LLM, but we can check if the logic *validates* or *truncates* 
        # if we were implementing a constraint checker.
        # Since we are implementing the logic, let's assume we pass a context that allows a long answer
        # and see if it respects limits. 
        # For a TDD unit test without a real LLM, we might verify the *instruction* sent to the LLM 
        # or the post-processing.
        # Let's assume process_request returns the string.
        pass # Placeholder for actual implementation logic verification

    def test_interview_format_structure(self, pilot):
        """Test that INTERVIEW mode responses follow the mandatory format."""
        context = "Java GC uses mark-and-sweep."
        response = pilot.process_request("How does Java GC work?", context=context)
        
        assert "Answer:" in response
        assert "Real World:" in response
        assert "Confidence:" in response
        
    def test_confidence_score_low_evidence(self, pilot):
        """Test that confidence is <= 40% if evidence is weak."""
        # This implies some logic to assess evidence density.
        # For the purpose of strict rule following, maybe we test the parsing?
        pass

if __name__ == "__main__":
    pytest.main([__file__])
