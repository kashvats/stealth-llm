import sys
import os
sys.path.append(os.getcwd())
from knowledge_base import KnowledgeBase

# Test 1: Fuzzy Lookup
kb = KnowledgeBase("dsa.json")
test_q = "Two Sum: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
match = kb.lookup(test_q)
if match:
    print(f"SUCCESS: Found Two Sum! (ID: {match['id']})")
else:
    print("FAILURE: Two Sum not found.")

# Test 2: Substring Lookup
test_q_short = "Valid Parentheses: Determine if the input string is valid."
match = kb.lookup(test_q_short)
if match:
    print(f"SUCCESS: Found Valid Parentheses via substring!")
else:
    print("FAILURE: Substring match failed.")

# Test 3: Cache New Entry
new_q = "Test Question: What is 1+1?"
new_a = "The answer is 2. [X]"
kb.add_entry(new_q, new_a)

kb_reload = KnowledgeBase("dsa.json")
if any(item['question'] == new_q for item in kb_reload.data):
    print("SUCCESS: New entry cached and reloaded!")
else:
    print("FAILURE: New entry not persisted.")
