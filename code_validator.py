import re
import subprocess
import json
import logging
import tempfile
import os
from typing import Tuple

logger = logging.getLogger(__name__)

class CodeValidator:
    TIMEOUT = 5  # seconds
    MAX_OUTPUT = 1024  # bytes

    @staticmethod
    def extract_python_code(text: str) -> str:
        """Extracts the first python code block found in markdown."""
        pattern = r"```python\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def validate_logic(code: str, test_input: str, expected_output: str) -> Tuple[bool, str]:
        """Safely validates Python code using subprocess sandbox."""
        if not code:
            return False, "No code found to validate."

        try:
            clean_input = re.sub(r"^[a-zA-Z0-9_]+\s*[=:]\s*", "", test_input.strip())
            clean_expected = expected_output.replace("nums =", "").replace("_", "None").strip()
            clean_expected = re.sub(r"^[a-zA-Z0-9_]+\s*[=:]\s*", "", clean_expected)

            if "," in clean_expected and "[" not in clean_expected:
                clean_expected = f"({clean_expected})"

            func_match = re.search(r"def (\w+)\(", code)
            if not func_match:
                return False, "Could not find a function to call."
            func_name = func_match.group(1)

            script = CodeValidator._build_validation_script(code, func_name, clean_input, clean_expected)
            return CodeValidator._run_in_sandbox(script)

        except Exception as e:
            logger.error(f"Validation setup failed: {e}")
            return False, f"Validation system error: {str(e)}"

    @staticmethod
    def _build_validation_script(code: str, func_name: str, test_input: str, expected_output: str) -> str:
        """Builds the validation script with input/output comparison."""
        return f"""
import json
import ast

{code}

def flexible_compare(actual, expected):
    if actual == expected: return True
    if isinstance(actual, int) and isinstance(expected, (list, tuple)) and len(expected) > 0:
        if actual == expected[0]: return True
    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        if len(actual) < len(expected): return False
        for a, e in zip(actual, expected):
            if e is not None and a != e: return False
        return True
    return str(actual).strip() == str(expected).strip()

try:
    t_input = {json.dumps(test_input)}
    if t_input.strip().startswith('[') or t_input.strip().startswith('{{'):
        args = ast.literal_eval(t_input)
    elif "," in t_input and "=" not in t_input:
        args = ast.literal_eval(f"({{t_input}})")
    else:
        try:
            args = ast.literal_eval(t_input)
        except:
            args = t_input

    try:
        expected = ast.literal_eval({json.dumps(expected_output)})
    except:
        expected = {json.dumps(expected_output)}

    if isinstance(args, tuple):
        actual = {func_name}(*args)
    else:
        actual = {func_name}(args)

    if flexible_compare(actual, expected):
        print("SUCCESS")
    else:
        print(f"FAILURE: Got {{actual}}, Expected {{expected}}")
except Exception as e:
    print(f"EXECUTION_ERROR: {{e}}")
"""

    @staticmethod
    def _run_in_sandbox(script: str) -> Tuple[bool, str]:
        """Executes script in isolated subprocess with timeout and resource limits."""
        try:
            result = subprocess.run(
                ["python", "-c", script],
                capture_output=True,
                text=True,
                timeout=CodeValidator.TIMEOUT,
                cwd=None
            )

            output = result.stdout.strip()[:CodeValidator.MAX_OUTPUT]

            if result.returncode != 0:
                error_msg = result.stderr.strip()[:CodeValidator.MAX_OUTPUT]
                logger.warning(f"Validation execution error: {error_msg}")
                return False, f"Execution error: {error_msg}"

            if "SUCCESS" in output:
                return True, "Passed"
            elif "FAILURE" in output:
                return False, output
            elif "EXECUTION_ERROR" in output:
                return False, output
            else:
                logger.warning(f"Unexpected validation output: {output}")
                return False, f"Validation system error: {output}"

        except subprocess.TimeoutExpired:
            logger.error("Code validation timed out (infinite loop?)")
            return False, "Timeout: Code took too long to execute (possible infinite loop)"
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return False, f"Sandbox error: {str(e)}"
