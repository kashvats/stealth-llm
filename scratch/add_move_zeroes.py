import json
import os

file_path = 'dsa.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_entry = {
    "id": max(item.get("id", 0) for item in data) + 1,
    "question": "Move Zeroes: Given an integer array nums, move all 0s to the end of it while maintaining the relative order of the non-zero elements.",
    "answer": "We use a two-pointer approach. We maintain a pointer 'non_zero' to track where the next non-zero element should go. We iterate through the array with 'idx': whenever we find a non-zero element, we swap it with the element at 'non_zero' and increment 'non_zero'. Time: O(n), Space: O(1).\n\n```python\ndef move_zeroes(nums):\n    non_zero = 0\n    for idx in range(len(nums)):\n        if nums[idx] != 0:\n            nums[non_zero], nums[idx] = nums[idx], nums[non_zero]\n            non_zero += 1\n``` [X]",
    "category": "DSA",
    "topic": "Two Pointers",
    "difficulty": "Easy",
    "tags": ["leetcode", "array", "two-pointers"]
}

data.append(new_entry)
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print("Successfully updated dsa.json with Move Zeroes.")
