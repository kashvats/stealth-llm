import pytest
from code_validator import CodeValidator


class TestCodeExtraction:
    """Tests for Python code extraction from markdown."""

    def test_extract_valid_python_block(self):
        text = "Here's the solution:\n```python\ndef two_sum(nums, target):\n    return [0, 1]\n```\nDone!"
        code = CodeValidator.extract_python_code(text)
        assert "def two_sum" in code
        assert "return [0, 1]" in code

    def test_extract_no_code_block(self):
        text = "This is just plain text with no code."
        code = CodeValidator.extract_python_code(text)
        assert code == ""

    def test_extract_first_block_only(self):
        text = "```python\ndef first():\n    pass\n```\n```python\ndef second():\n    pass\n```"
        code = CodeValidator.extract_python_code(text)
        assert "first" in code
        assert "second" not in code

    def test_extract_multiline_code(self):
        text = "```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n```"
        code = CodeValidator.extract_python_code(text)
        assert "factorial" in code
        assert "if n <= 1" in code


class TestCodeValidation:
    """Tests for code logic validation."""

    def test_valid_two_sum_solution(self):
        code = """
def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""
        success, msg = CodeValidator.validate_logic(code, "[2, 7, 11, 15]", "[0, 1]")
        assert success is True
        assert "Passed" in msg

    def test_invalid_solution_wrong_output(self):
        code = """
def twoSum(nums, target):
    return [0, 0]
"""
        success, msg = CodeValidator.validate_logic(code, "[2, 7, 11, 15]", "[0, 1]")
        assert success is False
        assert "FAILURE" in msg or "Got" in msg

    def test_no_function_found(self):
        code = "x = 5"
        success, msg = CodeValidator.validate_logic(code, "[1, 2]", "1")
        assert success is False
        assert "Could not find a function" in msg

    def test_empty_code(self):
        success, msg = CodeValidator.validate_logic("", "[1, 2]", "1")
        assert success is False
        assert "No code found" in msg

    def test_syntax_error_in_code(self):
        code = """
def broken(nums):
    return nums[  # syntax error
"""
        success, msg = CodeValidator.validate_logic(code, "[1, 2]", "1")
        assert success is False

    def test_infinite_loop_timeout(self):
        code = """
def infinite():
    while True:
        pass
    return 1
"""
        success, msg = CodeValidator.validate_logic(code, "[]", "1")
        assert success is False
        assert "Timeout" in msg or "too long" in msg

    def test_runtime_error(self):
        code = """
def divideByZero():
    return 1 / 0
"""
        success, msg = CodeValidator.validate_logic(code, "[]", "anything")
        assert success is False

    def test_list_comparison(self):
        code = """
def reverseList(arr):
    return arr[::-1]
"""
        success, msg = CodeValidator.validate_logic(code, "[1, 2, 3]", "[3, 2, 1]")
        assert success is True

    def test_single_value_extraction(self):
        code = """
def addOne(x):
    return x + 1
"""
        success, msg = CodeValidator.validate_logic(code, "5", "6")
        assert success is True

    def test_tuple_unpacking(self):
        code = """
def sum_two(a, b):
    return a + b
"""
        success, msg = CodeValidator.validate_logic(code, "3, 4", "7")
        assert success is True

    def test_flexible_compare_none_wildcard(self):
        code = """
def returns_tuple():
    return (1, 2, 3)
"""
        success, msg = CodeValidator.validate_logic(code, "[]", "(1, 2, 3)")
        assert success is True

    def test_nested_data_structures(self):
        code = """
def nested():
    return {"a": [1, 2], "b": [3, 4]}
"""
        success, msg = CodeValidator.validate_logic(code, "[]", """{"a": [1, 2], "b": [3, 4]}""")
        assert success is True


class TestInputSanitization:
    """Tests for input/output sanitization."""

    def test_sanitize_input_with_var_name(self):
        code = """
def identity(x):
    return x
"""
        success, msg = CodeValidator.validate_logic(code, "nums = [1, 2, 3]", "[1, 2, 3]")
        assert success is True

    def test_sanitize_output_with_underscore(self):
        code = """
def returns_none():
    return None
"""
        success, msg = CodeValidator.validate_logic(code, "[]", "_")
        assert success is True

    def test_sanitize_complex_output(self):
        code = """
def process():
    return (5, 10)
"""
        success, msg = CodeValidator.validate_logic(code, "[]", "5, 10")
        assert success is True


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_very_long_output(self):
        code = """
def long_list():
    return list(range(1000))
"""
        success, msg = CodeValidator.validate_logic(code, "[]", str(list(range(1000))))
        assert success is True

    def test_code_with_imports(self):
        code = """
import math
def circle_area(radius):
    return math.pi * radius ** 2
"""
        success, msg = CodeValidator.validate_logic(code, "1", "3.14159265")
        # Should not fail due to imports
        assert "error" not in msg.lower() or success is True

    def test_negative_numbers(self):
        code = """
def negate(x):
    return -x
"""
        success, msg = CodeValidator.validate_logic(code, "-5", "5")
        assert success is True

    def test_float_precision(self):
        code = """
def half(x):
    return x / 2
"""
        success, msg = CodeValidator.validate_logic(code, "10", "5")
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
