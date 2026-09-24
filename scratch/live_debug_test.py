import sys
import os
import json
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

# Setup logging to terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger("DEBUG_AUDIT")

from main import StealthPilotApp
from code_validator import CodeValidator

def live_debug():
    load_dotenv()
    print("\n" + "="*50)
    print("LIVE DEBUG AUDIT: TESTING RECENT FIXES")
    print("="*50)

    # 1. Initialize Components
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase("dsa.json")
    
    # Use the actual Ollama Client logic
    from llm_client import OllamaClient
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    client = OllamaClient(model=model)
    
    # 2. Test Input (The one the user is struggling with)
    test_input_text = "nums = [0,0,1,1,1,2,2,3,3,4]. Solve Remove Duplicates from Sorted Array."
    expected_output = "5, nums = [0,1,2,3,4,_,_,_,_,_]"
    
    print(f"\n[1] INPUT DETECTED:\n{test_input_text}")
    print(f"\n[2] EXPECTED OUTPUT:\n{expected_output}")

    # 3. Simulate Classification & Prompting
    pattern_list = ", ".join([p["id"] for p in kb.patterns])
    system_prompt = (
        f"You are an elite software engineer. Analyze the provided input (text or code).\n"
        f"1. Determine the core DSA problem being solved.\n"
        f"2. If it matches a pattern in this list: [{pattern_list}], you MUST start your response with 'PATTERN_ID: <ID>'.\n"
        f"3. Then provide a professional, optimized Python solution. Speak in the first person ('I')."
    )
    
    print("\n[3] CALLING LLM (Llama 3.2 3B)...")
    answer = client.ask(test_input_text, system_prompt=system_prompt)
    print(f"\n[4] LLM RAW RESPONSE:\n{answer}")

    # 4. Simulate Golden Injection
    import re
    if "PATTERN_ID:" in answer:
        try:
            p_id = answer.split("PATTERN_ID:")[1].split()[0].strip().replace(",", "").replace(".", "")
            golden_algo = kb.get_pattern(p_id)
            if golden_algo:
                print(f"\n[5] GOLDEN INJECTION TRIGGERED: {p_id}")
                golden_md = f"\n\n```python\n{golden_algo['code']}\n```\n*(Golden Solution Injected)*"
                answer = re.sub(r"```python\n.*?\n```", golden_md, answer, flags=re.DOTALL)
                print("  - Injection Successful!")
        except Exception as e:
            print(f"  - Injection Failed: {e}")

    # 5. Simulate Code Validation
    print("\n[6] EXTRACTING CODE FOR VALIDATION...")
    code = CodeValidator.extract_python_code(answer)
    if code:
        print(f"  - Code extracted successfully ({len(code)} chars)")
        print("\n[7] RUNNING FLEXIBLE VALIDATOR...")
        
        # We need to extract the actual test input part from the prompt
        # For simplicity in this debug script, we'll use a hardcoded test case
        actual_test_input = "[0,0,1,1,1,2,2,3,3,4]"
        
        success, feedback = CodeValidator.validate_logic(code, actual_test_input, expected_output)
        
        if success:
            print("  VALIDATION PASSED!")
            print(f"  Feedback: {feedback}")
        else:
            print("  VALIDATION FAILED!")
            print(f"  Feedback: {feedback}")
    else:
        print("  No code found in response.")

    print("\n" + "="*50)
    print("DEBUG AUDIT COMPLETE")
    print("="*50)

if __name__ == "__main__":
    live_debug()
