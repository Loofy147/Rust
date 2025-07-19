import os
import json
from datetime import datetime

class MinimalRealDataCollector:
    """A minimal version of the collector to produce essential data files."""
    def __init__(self, output_dir: str = "data/real_data"):
        self.output_dir = output_dir
        os.makedirs(os.path.join(self.output_dir, "algorithms"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "challenges"), exist_ok=True)

    def collect_all(self):
        self.collect_algorithm_implementations()
        self.collect_coding_challenges()
        print("✅ Minimal data collection finished.")

    def collect_algorithm_implementations(self):
        """Generates a sample of curated algorithm data."""
        print("🧮 Collecting algorithm implementations...")
        algorithms = [
            {
                'name': 'Quick Sort', 'type': 'Sorting', 'time_complexity': 'O(n log n)', 'space_complexity': 'O(log n)',
                'description': 'Divide-and-conquer sorting algorithm',
                'implementation': 'def quicksort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)',
                'source': 'algorithm_collection', 'collected_at': datetime.now().isoformat()
            },
            {
                'name': 'Binary Search', 'type': 'Searching', 'time_complexity': 'O(log n)', 'space_complexity': 'O(1)',
                'description': 'Efficient search algorithm for sorted arrays',
                'implementation': 'def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: left = mid + 1\n        else: right = mid - 1\n    return -1',
                'source': 'algorithm_collection', 'collected_at': datetime.now().isoformat()
            }
        ]
        output_file = os.path.join(self.output_dir, "algorithms", "implementations.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(algorithms, f, ensure_ascii=False, indent=2)
        print(f"   -> Saved to {output_file}")

    def collect_coding_challenges(self):
        """Generates a sample of curated coding challenges."""
        print("🎯 Collecting coding challenges...")
        challenges = [
            {
                'id': 'two_sum', 'title': 'Two Sum', 'difficulty': 'Easy', 'category': 'Array',
                'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
                'solution': 'def two_sum_optimized(nums, target):\n    num_map = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in num_map:\n            return [num_map[complement], i]\n        num_map[num] = i\n    return []',
                'topics': ['Array', 'Hash Table'], 'source': 'leetcode_style', 'collected_at': datetime.now().isoformat()
            }
        ]
        output_file = os.path.join(self.output_dir, "challenges", "coding_challenges.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(challenges, f, ensure_ascii=False, indent=2)
        print(f"   -> Saved to {output_file}")

collector = MinimalRealDataCollector()
collector.collect_all()
