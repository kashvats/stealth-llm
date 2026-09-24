import json
import os

file_path = 'dsa.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_entry = {
    "id": max(item.get("id", 0) for item in data) + 1,
    "question": "Merge Sorted Array: Given two sorted integer arrays nums1 and nums2, merge nums2 into nums1 as one sorted array in-place.",
    "answer": "To merge in-place without using extra space, we use three pointers starting from the END of the arrays. Since the end of `nums1` is empty (filled with zeros), we compare elements from the end of `nums1` and `nums2` and place the larger one at the very end of `nums1`. This avoids overwriting values we still need. Time: O(m + n), Space: O(1).\n\n```python\ndef merge(nums1, m, nums2, n):\n    i, j, k = m - 1, n - 1, m + n - 1\n    while i >= 0 and j >= 0:\n        if nums1[i] > nums2[j]:\n            nums1[k] = nums1[i]\n            i -= 1\n        else:\n            nums1[k] = nums2[j]\n            j -= 1\n        k -= 1\n    # If nums2 still has elements, copy them\n    while j >= 0:\n        nums1[k] = nums2[j]\n        j -= 1\n        k -= 1\n``` [X]",
    "category": "DSA",
    "topic": "Two Pointers",
    "difficulty": "Easy",
    "tags": ["leetcode", "array", "in-place"]
}

data.append(new_entry)
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print("Successfully updated dsa.json with Merge Sorted Array.")
