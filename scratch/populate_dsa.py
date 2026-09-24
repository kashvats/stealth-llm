import json
import os

file_path = 'dsa.json'
if not os.path.exists(file_path):
    data = []
else:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

# Keep original 50 items
data = [item for item in data if item.get('id', 0) <= 50]

new_questions = [
    {
        "question": "Diameter of Binary Tree: Given the root of a binary tree, return the length of the diameter of the tree.",
        "answer": "The diameter is the max value of (left_height + right_height) across all nodes. Use a bottom-up DFS that returns height and updates a global max. Time: O(n), Space: O(h).",
        "counterQuestion": "Does the longest path always pass through the root?",
        "counterQuestionAnswer": "No, it can be entirely within a subtree.",
        "topic": "Trees", "difficulty": "Easy"
    },
    {
        "question": "Subsets: Given an integer array nums of unique elements, return all possible subsets.",
        "answer": "Use Backtracking. At each element, either include it or skip it. Time: O(n * 2^n), Space: O(n).",
        "counterQuestion": "How many subsets are in a set of size n?",
        "counterQuestionAnswer": "2^n subsets.",
        "topic": "Backtracking", "difficulty": "Medium"
    },
    {
        "question": "Combination Sum: Find all unique combinations that sum to target.",
        "answer": "Use DFS with backtracking. Since elements can be reused, stay at the same index in recursive calls after adding an element. Time: O(2^target).",
        "counterQuestion": "How do you avoid duplicate combinations?",
        "counterQuestionAnswer": "By only picking elements at or after the current index.",
        "topic": "Backtracking", "difficulty": "Medium"
    },
    {
        "question": "Permutations: Return all possible permutations of an array.",
        "answer": "Backtracking with a 'used' set. Iterate through all numbers; if not used, add to path, recurse, then backtrack. Time: O(n * n!).",
        "counterQuestion": "How to handle duplicates in the input?",
        "counterQuestionAnswer": "Sort and skip duplicates if the previous identical element hasn't been used.",
        "topic": "Backtracking", "difficulty": "Medium"
    },
    {
        "question": "Kth Largest Element in an Array: Return the kth largest element.",
        "answer": "Use a Min-Heap of size k (O(n log k)) or QuickSelect (O(n) avg). Time: O(n) avg.",
        "counterQuestion": "When is a Heap better?",
        "counterQuestionAnswer": "When handling a live stream of data.",
        "topic": "Heap", "difficulty": "Medium"
    },
    {
        "question": "Rotting Oranges: Min minutes until no fresh oranges remain.",
        "answer": "BFS. Push all rotten oranges into queue. Level-by-level BFS increments time and rots neighbors. Time: O(m*n).",
        "counterQuestion": "Why BFS?",
        "counterQuestionAnswer": "BFS finds the shortest path (min time) in an unweighted graph with multiple sources.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Longest Increasing Subsequence: Length of LIS in array.",
        "answer": "DP: dp[i] is LIS ending at i. Check all j < i. Time: O(n^2). Binary search version is O(n log n).",
        "counterQuestion": "Can you reconstruct the sequence?",
        "counterQuestionAnswer": "Yes, using a parent pointer array.",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Word Ladder: Shortest transformation sequence from beginWord to endWord.",
        "answer": "BFS on unweighted graph. Change each letter and check dictionary. Time: O(n * m^2).",
        "counterQuestion": "How to optimize neighbor search?",
        "counterQuestionAnswer": "Use pattern-based hashing (e.g., '*ot').",
        "topic": "Graphs", "difficulty": "Hard"
    },
    {
        "question": "Unique Paths: Number of paths to reach bottom-right of m x n grid.",
        "answer": "DP: dp[i][j] = dp[i-1][j] + dp[i][j-1]. Or use combinatorics: (m+n-2)C(m-1).",
        "counterQuestion": "What if there are obstacles?",
        "counterQuestionAnswer": "Set dp[i][j] to 0 for obstacle cells.",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Binary Tree Right Side View: Nodes seen from the right.",
        "answer": "BFS: last node of each level. DFS: Root-Right-Left, first node seen at each depth. Time: O(n).",
        "counterQuestion": "Which is better for space in a wide tree?",
        "counterQuestionAnswer": "DFS is better for space in wide trees.",
        "topic": "Trees", "difficulty": "Medium"
    },
    {
        "question": "Longest Palindromic Substring: Return longest palindrome in s.",
        "answer": "Expand around center for each char/gap. Time: O(n^2). Manacher's is O(n).",
        "counterQuestion": "How to use DP?",
        "counterQuestionAnswer": "dp[i][j] is true if s[i:j+1] is a palindrome.",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Course Schedule II: Return the ordering of courses.",
        "answer": "BFS Topological Sort (Kahn's). If result size != numCourses, return empty. Time: O(V+E).",
        "counterQuestion": "What does a cycle mean?",
        "counterQuestionAnswer": "It means a circular dependency, impossible to complete.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Task Scheduler: Min intervals to finish tasks with cooldown n.",
        "answer": "Max-Heap and frequency map. Idle slots determined by most frequent task. Time: O(n).",
        "counterQuestion": "What if n=0?",
        "counterQuestionAnswer": "Result is just the total number of tasks.",
        "topic": "Heap", "difficulty": "Medium"
    },
    {
        "question": "Search a 2D Matrix: Target in sorted m x n matrix.",
        "answer": "If strictly sorted, treat as 1D and binary search. If row/col sorted, start top-right and move left/down. Time: O(m+n).",
        "counterQuestion": "Why top-right?",
        "counterQuestionAnswer": "Provides a clear decision (smaller -> left, larger -> down).",
        "topic": "Binary Search", "difficulty": "Medium"
    },
    {
        "question": "Koko Eating Bananas: Min speed k to eat all bananas within h hours.",
        "answer": "Binary search on speed range [1, max_pile]. For each mid, check total hours. Time: O(n log(max_pile)).",
        "counterQuestion": "Lower bound for k?",
        "counterQuestionAnswer": "1 banana per hour or sum(piles)/h.",
        "topic": "Binary Search", "difficulty": "Medium"
    },
    {
        "question": "Merge K Sorted Lists: Merge k sorted linked lists.",
        "answer": "Min-Heap of list heads. Pop smallest, add to result, push next. Time: O(n log k).",
        "counterQuestion": "Divide and Conquer approach?",
        "counterQuestionAnswer": "Merge pairs of lists recursively. Also O(n log k).",
        "topic": "Linked List", "difficulty": "Hard"
    },
    {
        "question": "Sliding Window Maximum: Max in each sliding window of size k.",
        "answer": "Deque for indices in decreasing value order. Remove old and smaller indices. Time: O(n).",
        "counterQuestion": "Space complexity?",
        "counterQuestionAnswer": "O(k) for the deque.",
        "topic": "Sliding Window", "difficulty": "Hard"
    },
    {
        "question": "Trapping Rain Water: Rain water trapped between bars.",
        "answer": "Two Pointers with left_max and right_max. Move smaller max. Time: O(n), Space: O(1).",
        "counterQuestion": "Can you use a Stack?",
        "counterQuestionAnswer": "Yes, a monotonic decreasing stack.",
        "topic": "Two Pointers", "difficulty": "Hard"
    },
    {
        "question": "Minimum Window Substring: Min window in s containing all chars of t.",
        "answer": "Sliding Window with have/need counters. Expand right, shrink left. Time: O(n).",
        "counterQuestion": "How to check validity?",
        "counterQuestionAnswer": "Increment 'have' when a char's count matches required count.",
        "topic": "Sliding Window", "difficulty": "Hard"
    },
    {
        "question": "Reorder List: Reorder L0 -> Ln -> L1 -> Ln-1...",
        "answer": "Find middle, reverse second half, merge halves. Time: O(n), Space: O(1).",
        "counterQuestion": "How to reverse second half?",
        "counterQuestionAnswer": "Standard iterative linked list reversal.",
        "topic": "Linked List", "difficulty": "Medium"
    },
    {
        "question": "Copy List with Random Pointer: Deep copy with random pointers.",
        "answer": "Hash map (old -> new) or interleaving nodes and separating. Time: O(n).",
        "counterQuestion": "Space for interleaving?",
        "counterQuestionAnswer": "O(1) extra space.",
        "topic": "Linked List", "difficulty": "Medium"
    },
    {
        "question": "Max Product Subarray: Largest product subarray.",
        "answer": "Track current_max and current_min (swap on negative). Time: O(n), Space: O(1).",
        "counterQuestion": "Why track min?",
        "counterQuestionAnswer": "Negative * negative = positive (potential new max).",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Partition Equal Subset Sum: Partition array into two equal sums.",
        "answer": "0/1 Knapsack for target sum = total/2. Use set for reachable sums. Time: O(n * total).",
        "counterQuestion": "Odd sum case?",
        "counterQuestionAnswer": "Return false immediately.",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Coin Change II: Ways to make target using denominations.",
        "answer": "DP: for each coin, iterate coin to amount and increment dp[i]. Time: O(n * amount).",
        "counterQuestion": "Why coins first?",
        "counterQuestionAnswer": "To count combinations, not permutations.",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Longest Common Subsequence: Length of LCS between two strings.",
        "answer": "2D DP: If match, 1 + dp[i-1][j-1]. Else, max(up, left). Time: O(m*n).",
        "counterQuestion": "Space optimization?",
        "counterQuestionAnswer": "Use only two rows: O(min(m, n)).",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Longest Increasing Path in a Matrix: Return length of LIP.",
        "answer": "DFS with Memoization. Store LIP for each cell. Time: O(m*n).",
        "counterQuestion": "Base case?",
        "counterQuestionAnswer": "Cell with no larger neighbors (LIP = 1).",
        "topic": "Dynamic Programming", "difficulty": "Hard"
    },
    {
        "question": "Burst Balloons: Max coins from bursting balloons.",
        "answer": "Interval DP. Pick balloon k to burst last in interval [i, j]. Time: O(n^3).",
        "counterQuestion": "Why burst last?",
        "counterQuestionAnswer": "Keep boundaries intact for the internal subproblems.",
        "topic": "Dynamic Programming", "difficulty": "Hard"
    },
    {
        "question": "Min Cost to Connect All Points: MST problem.",
        "answer": "Prim's with Min-Heap or Kruskal's with Union-Find. Time: O(n^2 log n).",
        "counterQuestion": "Manhattan distance formula?",
        "counterQuestionAnswer": "|x1-x2| + |y1-y2|.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Network Delay Time: Signal travel time for all nodes to receive from k.",
        "answer": "Dijkstra's with Min-Heap. Return max of shortest paths. Time: O(E log V).",
        "counterQuestion": "Negative weight case?",
        "counterQuestionAnswer": "Use Bellman-Ford.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Swim in Rising Water: Min time to reach bottom-right.",
        "answer": "Modified Dijkstra. Heap distance is max(path_depth, current_depth). Time: O(n^2 log n).",
        "counterQuestion": "Binary search approach?",
        "counterQuestionAnswer": "Search time in [0, max_depth] and check reachability.",
        "topic": "Graphs", "difficulty": "Hard"
    },
    {
        "question": "Alien Dictionary: Order of characters in alien language.",
        "answer": "Build directed graph from word differences. BFS/DFS Topological Sort. Time: O(Total chars).",
        "counterQuestion": "Invalid case?",
        "counterQuestionAnswer": "Prefix after longer word or cycle found.",
        "topic": "Graphs", "difficulty": "Hard"
    },
    {
        "question": "Cheapest Flights Within K Stops: Min cost with at most k stops.",
        "answer": "Bellman-Ford for k+1 iterations. Time: O(k * E).",
        "counterQuestion": "Why not Dijkstra?",
        "counterQuestionAnswer": "Standard Dijkstra doesn't account for stop limit correctly.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Redundant Connection: Edge that can be removed to turn graph into tree.",
        "answer": "Union-Find. Edge creating a cycle is redundant. Time: O(E alpha(V)).",
        "counterQuestion": "Is the graph connected?",
        "counterQuestionAnswer": "Yes, otherwise it wouldn't become a single tree.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Count Good Nodes in Binary Tree: Node >= max in path from root.",
        "answer": "DFS. Pass max_so_far down. Increment if node.val >= max. Time: O(n).",
        "counterQuestion": "Space complexity?",
        "counterQuestionAnswer": "O(h) for the recursion stack.",
        "topic": "Trees", "difficulty": "Medium"
    },
    {
        "question": "Sudoku Solver: Fill board such that it is valid.",
        "answer": "Backtracking. Try 1-9 in empty cells. Check row, col, and 3x3 box. Time: O(9^81).",
        "counterQuestion": "How to optimize?",
        "counterQuestionAnswer": "Bitmasks to track row/col/box availability.",
        "topic": "Backtracking", "difficulty": "Hard"
    },
    {
        "question": "N-Queens: Place n non-attacking queens.",
        "answer": "Backtracking. Track cols and diagonals in sets. Time: O(n!).",
        "counterQuestion": "Diagonal representation?",
        "counterQuestionAnswer": "r+c and r-c.",
        "topic": "Backtracking", "difficulty": "Hard"
    },
    {
        "question": "Daily Temperatures: Wait time for warmer temp.",
        "answer": "Monotonic Decreasing Stack. Store indices. pop when warmer. Time: O(n).",
        "counterQuestion": "Space complexity?",
        "counterQuestionAnswer": "O(n) for the stack.",
        "topic": "Stack", "difficulty": "Medium"
    },
    {
        "question": "Evaluate Reverse Polish Notation: Eval RPN expression.",
        "answer": "Stack. Push numbers. Pop two for operators. Time: O(n).",
        "counterQuestion": "Operand order?",
        "counterQuestionAnswer": "Second popped is left operand.",
        "topic": "Stack", "difficulty": "Medium"
    },
    {
        "question": "Kth Smallest Element in a BST: Find kth smallest node.",
        "answer": "In-order traversal. Stop at kth element. Time: O(h+k).",
        "counterQuestion": "Constant space solution?",
        "counterQuestionAnswer": "Morris Traversal.",
        "topic": "Trees", "difficulty": "Medium"
    },
    {
        "question": "Valid Sudoku: Determine if a Sudoku board is valid.",
        "answer": "Use sets for rows, cols, and 3x3 boxes. One pass to check all numbers. Time: O(1) (fixed 9x9).",
        "counterQuestion": "Why 3x3 box index is `(r/3)*3 + c/3`?",
        "counterQuestionAnswer": "It maps the 9x9 grid into 9 distinct 3x3 blocks indexed 0-8.",
        "topic": "Arrays", "difficulty": "Medium"
    },
    {
        "question": "Decode Ways: Number of ways to decode string of digits.",
        "answer": "DP: ways[i] = ways[i-1] (if single digit valid) + ways[i-2] (if two digit valid). Time: O(n).",
        "counterQuestion": "Handling '0'?",
        "counterQuestionAnswer": "'0' only valid if preceded by '1' or '2'.",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Binary Tree Level Order Traversal: Return levels of tree nodes.",
        "answer": "BFS using Queue. Record queue size at each level. Time: O(n).",
        "counterQuestion": "Space complexity?",
        "counterQuestionAnswer": "O(w) where w is max width.",
        "topic": "Trees", "difficulty": "Medium"
    },
    {
        "question": "Binary Tree Maximum Path Sum: Max sum of any path.",
        "answer": "DFS returns max branch sum. update global max with `node.val + left + right`. Time: O(n).",
        "counterQuestion": "Can path have negative values?",
        "counterQuestionAnswer": "Yes, so return 0 if branch sum is negative.",
        "topic": "Trees", "difficulty": "Hard"
    },
    {
        "question": "Serialize and Deserialize BST: Efficient conversion to/from string.",
        "answer": "Pre-order DFS. BST property allows deserialization without null markers. Time: O(n).",
        "counterQuestion": "Why no null markers?",
        "counterQuestionAnswer": "Because BST values tell you where left/right children split.",
        "topic": "Trees", "difficulty": "Medium"
    },
    {
        "question": "Find Median from Data Stream: Add num and find median.",
        "answer": "Two Heaps: Max-Heap (small half), Min-Heap (large half). Time: O(log n) add.",
        "counterQuestion": "Find median complexity?",
        "counterQuestionAnswer": "O(1).",
        "topic": "Heap", "difficulty": "Hard"
    },
    {
        "question": "Palindromic Substrings: Count all palindromic substrings.",
        "answer": "Expand around centers. Time: O(n^2), Space: O(1).",
        "counterQuestion": "Manacher's complexity?",
        "counterQuestionAnswer": "O(n).",
        "topic": "Dynamic Programming", "difficulty": "Medium"
    },
    {
        "question": "Kth Largest Element in a Stream: Find kth largest dynamically.",
        "answer": "Min-Heap of size k. Heap top is kth largest. Time: O(log k).",
        "counterQuestion": "Why Min-Heap?",
        "counterQuestionAnswer": "It keeps the k largest elements; smallest of those is the kth largest.",
        "topic": "Heap", "difficulty": "Easy"
    },
    {
        "question": "Rotting Oranges: Min time to rot all fresh oranges.",
        "answer": "Multi-source BFS from all rotten oranges. Time: O(m*n).",
        "counterQuestion": "What if fresh oranges unreachable?",
        "counterQuestionAnswer": "Return -1.",
        "topic": "Graphs", "difficulty": "Medium"
    },
    {
        "question": "Valid Parentheses: Determine if string is valid.",
        "answer": "Stack. Push open, check matching on close. Time: O(n).",
        "counterQuestion": "Empty string case?",
        "counterQuestionAnswer": "Valid (true).",
        "topic": "Stack", "difficulty": "Easy"
    },
    {
        "question": "Merge Two Sorted Lists: Merge lists into one sorted.",
        "answer": "Dummy node and pointer. Compare heads and link smaller. Time: O(n+m).",
        "counterQuestion": "Iterative vs Recursive?",
        "counterQuestionAnswer": "Iterative is O(1) space; Recursive is O(n+m) stack space.",
        "topic": "Linked List", "difficulty": "Easy"
    }
]

# Assign IDs starting from 51
start_id = 51
for i, entry in enumerate(new_questions):
    entry['id'] = start_id + i
    entry['category'] = 'DSA'
    entry['tags'] = ['leetcode', 'most-asked']

data.extend(new_questions)

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f'Successfully added {len(new_questions)} new entries to dsa.json.')
