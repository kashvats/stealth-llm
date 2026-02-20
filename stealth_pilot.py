from enum import Enum, auto

class Mode(Enum):
    GENERAL = auto()
    INTERVIEW = auto()
    CODEBASE = auto()

class StealthPilot:

    def determine_mode(self, request: str) -> Mode:
        request_lower = request.lower()
        
        # Codebase keywords
        code_keywords = ["code", "refactor", "test", "function", "class", "debug", "build", "bazel", "pytest", "complexity", "o(n)"]
        if any(keyword in request_lower for keyword in code_keywords):
            return Mode.CODEBASE
            
        # Interview keywords
        interview_keywords = ["why", "how", "design", "system", "behavioral", "tradeoff", "architecture"]
        if any(keyword in request_lower for keyword in interview_keywords):
            return Mode.INTERVIEW
            
        if request_lower.startswith("design"):
             return Mode.INTERVIEW

        return Mode.GENERAL

    def process_request(self, request: str, context: str) -> str:
        if not context or not context.strip():
            return "No supporting information found in provided context."
            
        mode = self.determine_mode(request)
        
        # In a real implementation, this would call the LLM with the system prompt and context.
        # Here we return a mocked response that follows the constraints for testing purposes.
        
        if mode == Mode.GENERAL:
            # Simulate a general answer (max 120 words)
            return f"Based on the context: {context[:50]}... [General Answer]"
            
        elif mode in (Mode.INTERVIEW, Mode.CODEBASE):
            # Mandatory format
            return (
                f"Answer: Based on {context[:20]}...\n"
                "Real World: As seen in high-scale systems...\n"
                "Diff: Senior engineers would...\n"
                "Next: \n1. Scalability?\n2. Security?\n3. Cost?\n"
                "Confidence: 85%"
            )
            
        return "Error: Unknown mode"

