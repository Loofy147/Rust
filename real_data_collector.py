#!/usr/bin/env python3
"""
Real Data Collector for AI Seed Training
========================================

جامع البيانات الحقيقية من مستودعات مفتوحة المصدر ومصادر موثوقة
يجمع البيانات من GitHub, Kaggle, HuggingFace, وغيرها من المصادر

الاستخدام:
    python real_data_collector.py --source github --topic algorithms
    python real_data_collector.py --source kaggle --category machine-learning
    python real_data_collector.py --source all --limit 100
"""

import os
import json
import requests
import time
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import zipfile
import tarfile

class RealDataCollector:
    """جامع البيانات الحقيقية"""
    
    def __init__(self, output_dir: str = "data/real_data"):
        """تهيئة جامع البيانات"""
        self.output_dir = output_dir
        self.ensure_directories()
        
        # إعدادات API (يمكن تخصيصها)
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.kaggle_username = os.getenv('KAGGLE_USERNAME', '')
        self.kaggle_key = os.getenv('KAGGLE_KEY', '')
        
        # قوائم المواضيع والكلمات المفتاحية
        self.github_topics = [
            "algorithms", "data-structures", "machine-learning", "deep-learning",
            "python", "javascript", "web-development", "api", "database",
            "computer-vision", "natural-language-processing", "reinforcement-learning",
            "neural-networks", "tensorflow", "pytorch", "scikit-learn",
            "coding-challenges", "competitive-programming", "leetcode-solutions"
        ]
        
        self.programming_languages = [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust",
            "TypeScript", "Swift", "Kotlin", "PHP", "Ruby", "Scala", "R"
        ]
        
    def ensure_directories(self):
        """إنشاء المجلدات المطلوبة"""
        subdirs = [
            "github_repos", "kaggle_datasets", "huggingface_datasets",
            "algorithms", "challenges", "documentation", "code_samples",
            "processed", "metadata"
        ]
        
        for subdir in subdirs:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
    
    def collect_github_repositories(self, topics: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """جمع مستودعات GitHub حسب المواضيع"""
        print(f"🔍 Collecting GitHub repositories for topics: {', '.join(topics)}")
        
        repositories = []
        headers = {}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        for topic in topics:
            try:
                # البحث عن المستودعات
                search_url = f"https://api.github.com/search/repositories"
                params = {
                    'q': f'topic:{topic} language:python stars:>10',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': min(limit, 100)
                }
                
                response = requests.get(search_url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    for repo in data.get('items', []):
                        repo_info = {
                            'id': repo['id'],
                            'name': repo['name'],
                            'full_name': repo['full_name'],
                            'description': repo.get('description', ''),
                            'language': repo.get('language', ''),
                            'stars': repo['stargazers_count'],
                            'forks': repo['forks_count'],
                            'topics': repo.get('topics', []),
                            'clone_url': repo['clone_url'],
                            'html_url': repo['html_url'],
                            'created_at': repo['created_at'],
                            'updated_at': repo['updated_at'],
                            'size': repo['size'],
                            'collected_topic': topic,
                            'collected_at': datetime.now().isoformat()
                        }
                        repositories.append(repo_info)
                        
                        # جمع معلومات إضافية عن المستودع
                        self._collect_repo_details(repo_info, headers)
                
                # تأخير لتجنب rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error collecting repositories for topic {topic}: {e}")
        
        # حفظ البيانات
        output_file = os.path.join(self.output_dir, "github_repos", "repositories.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(repositories, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Collected {len(repositories)} repositories")
        return repositories
    
    def _collect_repo_details(self, repo_info: Dict[str, Any], headers: Dict[str, str]):
        """جمع تفاصيل إضافية عن المستودع"""
        try:
            # جمع معلومات الملفات
            contents_url = f"https://api.github.com/repos/{repo_info['full_name']}/contents"
            response = requests.get(contents_url, headers=headers)
            
            if response.status_code == 200:
                contents = response.json()
                repo_info['files'] = []
                
                for item in contents:
                    if item['type'] == 'file':
                        file_info = {
                            'name': item['name'],
                            'path': item['path'],
                            'size': item['size'],
                            'download_url': item.get('download_url')
                        }
                        repo_info['files'].append(file_info)
                        
                        # تحميل ملفات مهمة
                        if item['name'].lower() in ['readme.md', 'requirements.txt', 'setup.py', 'package.json']:
                            self._download_file(item, repo_info['full_name'])
            
            # جمع معلومات اللغات المستخدمة
            languages_url = f"https://api.github.com/repos/{repo_info['full_name']}/languages"
            response = requests.get(languages_url, headers=headers)
            
            if response.status_code == 200:
                repo_info['languages'] = response.json()
            
            time.sleep(0.5)  # تأخير قصير
            
        except Exception as e:
            print(f"⚠️ Warning: Could not collect details for {repo_info['full_name']}: {e}")
    
    def _download_file(self, file_info: Dict[str, Any], repo_name: str):
        """تحميل ملف من GitHub"""
        try:
            if file_info.get('download_url'):
                response = requests.get(file_info['download_url'])
                if response.status_code == 200:
                    # إنشاء مجلد للمستودع
                    repo_dir = os.path.join(self.output_dir, "github_repos", repo_name.replace('/', '_'))
                    os.makedirs(repo_dir, exist_ok=True)
                    
                    # حفظ الملف
                    file_path = os.path.join(repo_dir, file_info['name'])
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"📁 Downloaded: {file_info['name']} from {repo_name}")
        except Exception as e:
            print(f"❌ Error downloading {file_info['name']}: {e}")
    
    def collect_algorithm_implementations(self) -> List[Dict[str, Any]]:
        """جمع تطبيقات الخوارزميات من مصادر مختلفة"""
        print("🧮 Collecting algorithm implementations...")
        
        algorithms = []
        
        # خوارزميات الترتيب
        sorting_algorithms = [
            {
                'name': 'Quick Sort',
                'type': 'Sorting',
                'time_complexity': 'O(n log n) average, O(n²) worst',
                'space_complexity': 'O(log n)',
                'description': 'Divide-and-conquer sorting algorithm',
                'implementation': '''
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)

# Test cases
test_cases = [
    [3, 6, 8, 10, 1, 2, 1],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [],
    [1]
]

for test in test_cases:
    print(f"Input: {test}")
    print(f"Output: {quicksort(test.copy())}")
''',
                'use_cases': ['General purpose sorting', 'In-place sorting when memory is limited'],
                'pros': ['Fast average case', 'In-place sorting possible'],
                'cons': ['Poor worst-case performance', 'Not stable'],
                'source': 'algorithm_collection',
                'collected_at': datetime.now().isoformat()
            },
            {
                'name': 'Merge Sort',
                'type': 'Sorting',
                'time_complexity': 'O(n log n)',
                'space_complexity': 'O(n)',
                'description': 'Stable divide-and-conquer sorting algorithm',
                'implementation': '''
def mergesort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Test cases
test_cases = [
    [3, 6, 8, 10, 1, 2, 1],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [],
    [1]
]

for test in test_cases:
    print(f"Input: {test}")
    print(f"Output: {mergesort(test.copy())}")
''',
                'use_cases': ['When stability is required', 'External sorting'],
                'pros': ['Stable', 'Guaranteed O(n log n)', 'Good for linked lists'],
                'cons': ['Requires extra space', 'Slower than quicksort in practice'],
                'source': 'algorithm_collection',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        algorithms.extend(sorting_algorithms)
        
        # خوارزميات البحث
        search_algorithms = [
            {
                'name': 'Binary Search',
                'type': 'Searching',
                'time_complexity': 'O(log n)',
                'space_complexity': 'O(1)',
                'description': 'Efficient search algorithm for sorted arrays',
                'implementation': '''
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

def binary_search_recursive(arr, target, left=0, right=None):
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = (left + right) // 2
    
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)

# Test cases
test_array = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
test_targets = [1, 7, 15, 19, 2, 20]

for target in test_targets:
    result = binary_search(test_array, target)
    print(f"Searching for {target}: {'Found at index ' + str(result) if result != -1 else 'Not found'}")
''',
                'use_cases': ['Searching in sorted arrays', 'Finding insertion point'],
                'pros': ['Very fast for sorted data', 'Simple to implement'],
                'cons': ['Requires sorted data', 'Not suitable for linked lists'],
                'source': 'algorithm_collection',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        algorithms.extend(search_algorithms)
        
        # خوارزميات الرسوم البيانية
        graph_algorithms = [
            {
                'name': 'Breadth-First Search (BFS)',
                'type': 'Graph Traversal',
                'time_complexity': 'O(V + E)',
                'space_complexity': 'O(V)',
                'description': 'Graph traversal algorithm that explores neighbors first',
                'implementation': '''
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    result = []
    
    while queue:
        vertex = queue.popleft()
        
        if vertex not in visited:
            visited.add(vertex)
            result.append(vertex)
            
            # Add unvisited neighbors to queue
            for neighbor in graph.get(vertex, []):
                if neighbor not in visited:
                    queue.append(neighbor)
    
    return result

def bfs_shortest_path(graph, start, goal):
    if start == goal:
        return [start]
    
    visited = set()
    queue = deque([(start, [start])])
    
    while queue:
        vertex, path = queue.popleft()
        
        if vertex not in visited:
            visited.add(vertex)
            
            for neighbor in graph.get(vertex, []):
                new_path = path + [neighbor]
                
                if neighbor == goal:
                    return new_path
                
                if neighbor not in visited:
                    queue.append((neighbor, new_path))
    
    return None

# Test graph
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E']
}

print("BFS traversal from A:", bfs(graph, 'A'))
print("Shortest path from A to F:", bfs_shortest_path(graph, 'A', 'F'))
''',
                'use_cases': ['Finding shortest path', 'Level-order traversal', 'Connected components'],
                'pros': ['Finds shortest path', 'Complete algorithm'],
                'cons': ['High memory usage', 'Not suitable for very large graphs'],
                'source': 'algorithm_collection',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        algorithms.extend(graph_algorithms)
        
        # حفظ البيانات
        output_file = os.path.join(self.output_dir, "algorithms", "implementations.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(algorithms, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Collected {len(algorithms)} algorithm implementations")
        return algorithms
    
    def collect_coding_challenges(self) -> List[Dict[str, Any]]:
        """جمع تحديات البرمجة من مصادر مختلفة"""
        print("🎯 Collecting coding challenges...")
        
        challenges = []
        
        # تحديات خوارزمية
        algorithmic_challenges = [
            {
                'id': 'two_sum',
                'title': 'Two Sum',
                'difficulty': 'Easy',
                'category': 'Array',
                'description': '''
Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.
''',
                'examples': [
                    {
                        'input': 'nums = [2,7,11,15], target = 9',
                        'output': '[0,1]',
                        'explanation': 'Because nums[0] + nums[1] == 9, we return [0, 1].'
                    },
                    {
                        'input': 'nums = [3,2,4], target = 6',
                        'output': '[1,2]',
                        'explanation': 'Because nums[1] + nums[2] == 6, we return [1, 2].'
                    }
                ],
                'constraints': [
                    '2 <= nums.length <= 10^4',
                    '-10^9 <= nums[i] <= 10^9',
                    '-10^9 <= target <= 10^9',
                    'Only one valid answer exists.'
                ],
                'solution': '''
def two_sum(nums, target):
    # Approach 1: Brute Force - O(n²)
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

def two_sum_optimized(nums, target):
    # Approach 2: Hash Map - O(n)
    num_map = {}
    
    for i, num in enumerate(nums):
        complement = target - num
        
        if complement in num_map:
            return [num_map[complement], i]
        
        num_map[num] = i
    
    return []

# Test cases
test_cases = [
    ([2, 7, 11, 15], 9),
    ([3, 2, 4], 6),
    ([3, 3], 6)
]

for nums, target in test_cases:
    result = two_sum_optimized(nums, target)
    print(f"nums = {nums}, target = {target} -> {result}")
''',
                'topics': ['Array', 'Hash Table'],
                'companies': ['Amazon', 'Google', 'Facebook', 'Microsoft'],
                'source': 'leetcode_style',
                'collected_at': datetime.now().isoformat()
            },
            {
                'id': 'reverse_linked_list',
                'title': 'Reverse Linked List',
                'difficulty': 'Easy',
                'category': 'Linked List',
                'description': '''
Given the head of a singly linked list, reverse the list, and return the reversed list.
''',
                'examples': [
                    {
                        'input': 'head = [1,2,3,4,5]',
                        'output': '[5,4,3,2,1]',
                        'explanation': 'The linked list is reversed.'
                    },
                    {
                        'input': 'head = [1,2]',
                        'output': '[2,1]',
                        'explanation': 'The linked list is reversed.'
                    }
                ],
                'constraints': [
                    'The number of nodes in the list is the range [0, 5000].',
                    '-5000 <= Node.val <= 5000'
                ],
                'solution': '''
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse_list_iterative(head):
    prev = None
    current = head
    
    while current:
        next_temp = current.next
        current.next = prev
        prev = current
        current = next_temp
    
    return prev

def reverse_list_recursive(head):
    if not head or not head.next:
        return head
    
    reversed_head = reverse_list_recursive(head.next)
    head.next.next = head
    head.next = None
    
    return reversed_head

# Helper function to create linked list from array
def create_linked_list(arr):
    if not arr:
        return None
    
    head = ListNode(arr[0])
    current = head
    
    for val in arr[1:]:
        current.next = ListNode(val)
        current = current.next
    
    return head

# Helper function to convert linked list to array
def linked_list_to_array(head):
    result = []
    current = head
    
    while current:
        result.append(current.val)
        current = current.next
    
    return result

# Test cases
test_cases = [
    [1, 2, 3, 4, 5],
    [1, 2],
    []
]

for test in test_cases:
    head = create_linked_list(test)
    reversed_head = reverse_list_iterative(head)
    result = linked_list_to_array(reversed_head)
    print(f"Input: {test} -> Output: {result}")
''',
                'topics': ['Linked List', 'Recursion'],
                'companies': ['Amazon', 'Microsoft', 'Apple', 'Facebook'],
                'source': 'leetcode_style',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        challenges.extend(algorithmic_challenges)
        
        # تحديات تطوير الويب
        web_challenges = [
            {
                'id': 'todo_app',
                'title': 'Build a Todo Application',
                'difficulty': 'Intermediate',
                'category': 'Web Development',
                'description': '''
Create a fully functional Todo application with the following features:
- Add new todos
- Mark todos as complete/incomplete
- Delete todos
- Filter todos (all, active, completed)
- Persist data in localStorage
- Responsive design
''',
                'requirements': [
                    'Use vanilla JavaScript or a framework of your choice',
                    'Implement CRUD operations',
                    'Add input validation',
                    'Include error handling',
                    'Make it responsive',
                    'Add keyboard shortcuts'
                ],
                'solution_structure': {
                    'html': 'Basic HTML structure with form and list',
                    'css': 'Responsive styling with modern design',
                    'javascript': 'Event handling, DOM manipulation, localStorage'
                },
                'bonus_features': [
                    'Drag and drop reordering',
                    'Due dates and reminders',
                    'Categories/tags',
                    'Search functionality',
                    'Export/import data'
                ],
                'topics': ['HTML', 'CSS', 'JavaScript', 'DOM', 'localStorage'],
                'estimated_time': '4-6 hours',
                'source': 'web_challenges',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        challenges.extend(web_challenges)
        
        # حفظ البيانات
        output_file = os.path.join(self.output_dir, "challenges", "coding_challenges.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(challenges, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Collected {len(challenges)} coding challenges")
        return challenges
    
    def collect_documentation_and_tutorials(self) -> List[Dict[str, Any]]:
        """جمع الوثائق والدروس التعليمية"""
        print("📚 Collecting documentation and tutorials...")
        
        docs = []
        
        # دروس الخوارزميات
        algorithm_tutorials = [
            {
                'title': 'Understanding Time and Space Complexity',
                'category': 'Algorithms',
                'level': 'Beginner',
                'content': '''
# Understanding Time and Space Complexity

## What is Time Complexity?

Time complexity is a way to describe how the runtime of an algorithm changes as the input size grows. It's expressed using Big O notation.

### Common Time Complexities:

1. **O(1) - Constant Time**
   - The algorithm takes the same amount of time regardless of input size
   - Example: Accessing an array element by index
   
2. **O(log n) - Logarithmic Time**
   - Runtime grows logarithmically with input size
   - Example: Binary search
   
3. **O(n) - Linear Time**
   - Runtime grows linearly with input size
   - Example: Linear search
   
4. **O(n log n) - Linearithmic Time**
   - Common in efficient sorting algorithms
   - Example: Merge sort, Quick sort (average case)
   
5. **O(n²) - Quadratic Time**
   - Runtime grows quadratically with input size
   - Example: Bubble sort, Selection sort
   
6. **O(2^n) - Exponential Time**
   - Runtime doubles with each additional input
   - Example: Recursive Fibonacci (naive implementation)

## What is Space Complexity?

Space complexity describes how much additional memory an algorithm uses as the input size grows.

### Examples:

```python
# O(1) Space - Constant space
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val

# O(n) Space - Linear space
def reverse_array(arr):
    return arr[::-1]  # Creates a new array

# O(log n) Space - Logarithmic space (recursive call stack)
def binary_search_recursive(arr, target, left=0, right=None):
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = (left + right) // 2
    
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)
```

## How to Analyze Complexity:

1. **Identify the basic operations** (comparisons, assignments, etc.)
2. **Count how many times these operations execute** relative to input size
3. **Focus on the worst-case scenario**
4. **Drop constants and lower-order terms**

## Practice Problems:

1. What's the time complexity of nested loops?
2. How does recursion affect space complexity?
3. Can you optimize a O(n²) algorithm to O(n log n)?
''',
                'topics': ['Algorithms', 'Complexity Analysis', 'Big O'],
                'prerequisites': ['Basic programming knowledge'],
                'estimated_reading_time': '15 minutes',
                'source': 'educational_content',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        docs.extend(algorithm_tutorials)
        
        # دروس تطوير الويب
        web_tutorials = [
            {
                'title': 'Modern JavaScript ES6+ Features',
                'category': 'Web Development',
                'level': 'Intermediate',
                'content': '''
# Modern JavaScript ES6+ Features

## Arrow Functions

Arrow functions provide a more concise syntax for writing functions:

```javascript
// Traditional function
function add(a, b) {
    return a + b;
}

// Arrow function
const add = (a, b) => a + b;

// With single parameter (parentheses optional)
const square = x => x * x;

// With no parameters
const greet = () => console.log('Hello!');

// With block body
const processData = (data) => {
    const processed = data.map(item => item * 2);
    return processed.filter(item => item > 10);
};
```

## Destructuring

Extract values from arrays and objects:

```javascript
// Array destructuring
const numbers = [1, 2, 3, 4, 5];
const [first, second, ...rest] = numbers;
console.log(first); // 1
console.log(rest);  // [3, 4, 5]

// Object destructuring
const person = { name: 'John', age: 30, city: 'New York' };
const { name, age } = person;
console.log(name); // 'John'

// With default values
const { country = 'USA' } = person;
console.log(country); // 'USA'

// Renaming variables
const { name: fullName } = person;
console.log(fullName); // 'John'
```

## Template Literals

String interpolation and multi-line strings:

```javascript
const name = 'Alice';
const age = 25;

// Template literal
const message = `Hello, my name is ${name} and I'm ${age} years old.`;

// Multi-line strings
const html = `
    <div class="card">
        <h2>${name}</h2>
        <p>Age: ${age}</p>
    </div>
`;

// Tagged template literals
function highlight(strings, ...values) {
    return strings.reduce((result, string, i) => {
        const value = values[i] ? `<mark>${values[i]}</mark>` : '';
        return result + string + value;
    }, '');
}

const highlighted = highlight`Name: ${name}, Age: ${age}`;
```

## Promises and Async/Await

Handle asynchronous operations:

```javascript
// Promise
function fetchData() {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            resolve('Data fetched successfully');
        }, 1000);
    });
}

// Using .then()
fetchData()
    .then(data => console.log(data))
    .catch(error => console.error(error));

// Using async/await
async function getData() {
    try {
        const data = await fetchData();
        console.log(data);
    } catch (error) {
        console.error(error);
    }
}

// Multiple async operations
async function fetchMultipleData() {
    try {
        const [users, posts, comments] = await Promise.all([
            fetch('/api/users').then(r => r.json()),
            fetch('/api/posts').then(r => r.json()),
            fetch('/api/comments').then(r => r.json())
        ]);
        
        return { users, posts, comments };
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}
```

## Modules

Import and export functionality:

```javascript
// math.js
export const PI = 3.14159;

export function add(a, b) {
    return a + b;
}

export function multiply(a, b) {
    return a * b;
}

// Default export
export default function subtract(a, b) {
    return a - b;
}

// main.js
import subtract, { PI, add, multiply } from './math.js';

// Import all
import * as math from './math.js';

console.log(math.PI);
console.log(math.add(2, 3));
```

## Classes

Object-oriented programming in JavaScript:

```javascript
class Animal {
    constructor(name, species) {
        this.name = name;
        this.species = species;
    }
    
    speak() {
        console.log(`${this.name} makes a sound`);
    }
    
    // Static method
    static getKingdom() {
        return 'Animalia';
    }
    
    // Getter
    get info() {
        return `${this.name} is a ${this.species}`;
    }
    
    // Setter
    set nickname(nick) {
        this._nickname = nick;
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name, 'Canine');
        this.breed = breed;
    }
    
    speak() {
        console.log(`${this.name} barks`);
    }
    
    fetch() {
        console.log(`${this.name} fetches the ball`);
    }
}

const dog = new Dog('Buddy', 'Golden Retriever');
dog.speak(); // 'Buddy barks'
console.log(dog.info); // 'Buddy is a Canine'
```

## Practice Exercises:

1. Convert traditional functions to arrow functions
2. Use destructuring to extract data from API responses
3. Create a class hierarchy for different types of vehicles
4. Build a simple async function that fetches data from multiple APIs
''',
                'topics': ['JavaScript', 'ES6+', 'Modern Web Development'],
                'prerequisites': ['Basic JavaScript knowledge'],
                'estimated_reading_time': '25 minutes',
                'source': 'educational_content',
                'collected_at': datetime.now().isoformat()
            }
        ]
        
        docs.extend(web_tutorials)
        
        # حفظ البيانات
        output_file = os.path.join(self.output_dir, "documentation", "tutorials.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Collected {len(docs)} documentation and tutorial items")
        return docs
    
    def generate_metadata_summary(self) -> Dict[str, Any]:
        """إنشاء ملخص البيانات المجمعة"""
        print("📊 Generating metadata summary...")
        
        summary = {
            'collection_date': datetime.now().isoformat(),
            'total_items': 0,
            'sources': {},
            'categories': {},
            'file_sizes': {},
            'statistics': {}
        }
        
        # فحص الملفات المجمعة
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        if isinstance(data, list):
                            count = len(data)
                            summary['total_items'] += count
                            
                            # تصنيف حسب المصدر
                            category = os.path.basename(root)
                            summary['categories'][category] = summary['categories'].get(category, 0) + count
                            
                            # حجم الملف
                            file_size = os.path.getsize(file_path)
                            summary['file_sizes'][file] = file_size
                            
                            # إحصائيات إضافية
                            if data and isinstance(data[0], dict):
                                for item in data:
                                    source = item.get('source', 'unknown')
                                    summary['sources'][source] = summary['sources'].get(source, 0) + 1
                    
                    except Exception as e:
                        print(f"⚠️ Warning: Could not process {file_path}: {e}")
        
        # حفظ الملخص
        summary_file = os.path.join(self.output_dir, "metadata", "collection_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Generated metadata summary: {summary['total_items']} total items")
        return summary

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="Collect real data for AI Seed training")
    parser.add_argument("--source", choices=["github", "algorithms", "challenges", "docs", "all"], 
                       default="all", help="Data source to collect from")
    parser.add_argument("--limit", type=int, default=50,
                       help="Limit number of items to collect")
    parser.add_argument("--output", default="data/real_data",
                       help="Output directory")
    
    args = parser.parse_args()
    
    collector = RealDataCollector(args.output)
    
    print(f"🚀 Starting real data collection...")
    print(f"📁 Output directory: {args.output}")
    
    if args.source in ["all", "github"]:
        print("🔍 Collecting GitHub repositories...")
        collector.collect_github_repositories(collector.github_topics[:5], args.limit)
    
    if args.source in ["all", "algorithms"]:
        print("🧮 Collecting algorithm implementations...")
        collector.collect_algorithm_implementations()
    
    if args.source in ["all", "challenges"]:
        print("🎯 Collecting coding challenges...")
        collector.collect_coding_challenges()
    
    if args.source in ["all", "docs"]:
        print("📚 Collecting documentation and tutorials...")
        collector.collect_documentation_and_tutorials()
    
    # إنشاء ملخص البيانات
    summary = collector.generate_metadata_summary()
    
    print("🎉 Real data collection completed!")
    print(f"📊 Total items collected: {summary['total_items']}")
    print(f"📂 Categories: {list(summary['categories'].keys())}")

if __name__ == "__main__":
    main()

