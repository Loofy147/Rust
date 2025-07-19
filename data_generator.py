#!/usr/bin/env python3
"""
Data Generator for AI Seed Training
===================================

هذا المولد ينشئ مجموعة غنية ومتنوعة من البيانات لتدريب بذرة الذكاء الاصطناعي
يشمل: JSONL, Tables, Training Data, Logs, Information, Techniques, 
Algorithms, Logic, Lessons, Creative Data, وغيرها.

الاستخدام:
    python data_generator.py --type all
    python data_generator.py --type jsonl --count 1000
    python data_generator.py --type tables --format csv
"""

import os
import json
import csv
import random
import datetime
import uuid
import argparse
from typing import Dict, List, Any, Optional
from faker import Faker
import pandas as pd
import numpy as np

# إعداد Faker للغة العربية والإنجليزية
fake_ar = Faker('ar_SA')
fake_en = Faker('en_US')
fake = fake_en  # الافتراضي

class DataGenerator:
    """مولد البيانات الرئيسي"""
    
    def __init__(self, output_dir: str = "data"):
        """تهيئة مولد البيانات"""
        self.output_dir = output_dir
        self.ensure_directories()
        
        # قوائم البيانات المرجعية
        self.programming_languages = [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", 
            "TypeScript", "Swift", "Kotlin", "PHP", "Ruby", "Scala", "R"
        ]
        
        self.algorithms_types = [
            "Sorting", "Searching", "Graph", "Dynamic Programming", 
            "Greedy", "Divide and Conquer", "Backtracking", "Tree Traversal",
            "String Matching", "Number Theory", "Geometry", "Machine Learning"
        ]
        
        self.difficulty_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        
        self.data_structures = [
            "Array", "Linked List", "Stack", "Queue", "Tree", "Graph", 
            "Hash Table", "Heap", "Trie", "Segment Tree", "Fenwick Tree"
        ]
        
        self.design_patterns = [
            "Singleton", "Factory", "Observer", "Strategy", "Command",
            "Adapter", "Decorator", "Facade", "Proxy", "Builder"
        ]
        
    def ensure_directories(self):
        """إنشاء المجلدات المطلوبة"""
        subdirs = [
            "training_data", "logs", "information", "techniques", 
            "algorithms", "logic", "lessons", "creative", "tables", 
            "jsonl", "misc"
        ]
        
        for subdir in subdirs:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
    
    def generate_jsonl_training_data(self, count: int = 1000) -> str:
        """توليد بيانات التدريب بصيغة JSONL"""
        output_file = os.path.join(self.output_dir, "jsonl", "training_data.jsonl")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i in range(count):
                # توليد مهمة برمجية
                task_type = random.choice(["algorithm", "web_dev", "data_analysis", "ml"])
                difficulty = random.choice([0.1, 0.3, 0.5, 0.7, 0.9])
                
                if task_type == "algorithm":
                    data = self._generate_algorithm_task(i, difficulty)
                elif task_type == "web_dev":
                    data = self._generate_web_dev_task(i, difficulty)
                elif task_type == "data_analysis":
                    data = self._generate_data_analysis_task(i, difficulty)
                else:  # ml
                    data = self._generate_ml_task(i, difficulty)
                
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        return output_file
    
    def _generate_algorithm_task(self, task_id: int, difficulty: float) -> Dict[str, Any]:
        """توليد مهمة خوارزمية"""
        algorithm_type = random.choice(self.algorithms_types)
        language = random.choice(self.programming_languages)
        
        # قوالب المهام حسب النوع
        if algorithm_type == "Sorting":
            problem = f"Implement an efficient sorting algorithm for an array of {random.randint(100, 10000)} integers"
            solution_template = """
def efficient_sort(arr):
    # Implementation here
    if len(arr) <= 1:
        return arr
    
    # Quick sort implementation
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return efficient_sort(left) + middle + efficient_sort(right)
"""
        elif algorithm_type == "Searching":
            problem = f"Implement binary search to find an element in a sorted array"
            solution_template = """
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
"""
        else:
            problem = f"Solve a {algorithm_type.lower()} problem with optimal time complexity"
            solution_template = f"# {algorithm_type} solution template\n# Implementation depends on specific problem"
        
        return {
            "task_id": f"algo_{task_id:06d}",
            "type": "algorithm",
            "difficulty": difficulty,
            "language": language,
            "algorithm_type": algorithm_type,
            "problem_statement": problem,
            "solution_template": solution_template,
            "time_complexity": self._get_time_complexity(algorithm_type),
            "space_complexity": self._get_space_complexity(algorithm_type),
            "test_cases": self._generate_test_cases(algorithm_type),
            "hints": self._generate_hints(algorithm_type),
            "tags": [algorithm_type.lower(), language.lower(), "algorithm"],
            "created_at": datetime.datetime.now().isoformat(),
            "estimated_time_minutes": int(difficulty * 120 + 30)
        }
    
    def _generate_web_dev_task(self, task_id: int, difficulty: float) -> Dict[str, Any]:
        """توليد مهمة تطوير ويب"""
        frameworks = ["React", "Vue", "Angular", "Flask", "Django", "Express", "FastAPI"]
        framework = random.choice(frameworks)
        
        features = [
            "user authentication", "responsive design", "API integration",
            "database operations", "real-time updates", "file upload",
            "search functionality", "pagination", "form validation"
        ]
        
        selected_features = random.sample(features, random.randint(2, 4))
        
        return {
            "task_id": f"web_{task_id:06d}",
            "type": "web_development",
            "difficulty": difficulty,
            "framework": framework,
            "problem_statement": f"Build a web application using {framework} with {', '.join(selected_features)}",
            "features": selected_features,
            "requirements": self._generate_web_requirements(framework, selected_features),
            "solution_structure": self._generate_web_structure(framework),
            "test_scenarios": self._generate_web_tests(selected_features),
            "tags": ["web", framework.lower(), "frontend" if framework in ["React", "Vue", "Angular"] else "backend"],
            "created_at": datetime.datetime.now().isoformat(),
            "estimated_time_minutes": int(difficulty * 240 + 60)
        }
    
    def _generate_data_analysis_task(self, task_id: int, difficulty: float) -> Dict[str, Any]:
        """توليد مهمة تحليل البيانات"""
        datasets = ["sales", "customer", "financial", "social_media", "sensor", "medical"]
        dataset_type = random.choice(datasets)
        
        analysis_types = [
            "descriptive statistics", "correlation analysis", "trend analysis",
            "clustering", "classification", "regression", "time series"
        ]
        
        analysis_type = random.choice(analysis_types)
        
        return {
            "task_id": f"data_{task_id:06d}",
            "type": "data_analysis",
            "difficulty": difficulty,
            "dataset_type": dataset_type,
            "analysis_type": analysis_type,
            "problem_statement": f"Perform {analysis_type} on {dataset_type} dataset",
            "data_description": self._generate_data_description(dataset_type),
            "analysis_steps": self._generate_analysis_steps(analysis_type),
            "expected_outputs": self._generate_expected_outputs(analysis_type),
            "tools": ["pandas", "numpy", "matplotlib", "seaborn", "scikit-learn"],
            "tags": ["data_analysis", dataset_type, analysis_type.replace(" ", "_")],
            "created_at": datetime.datetime.now().isoformat(),
            "estimated_time_minutes": int(difficulty * 180 + 45)
        }
    
    def _generate_ml_task(self, task_id: int, difficulty: float) -> Dict[str, Any]:
        """توليد مهمة تعلم آلة"""
        ml_types = ["supervised", "unsupervised", "reinforcement"]
        ml_type = random.choice(ml_types)
        
        if ml_type == "supervised":
            algorithms = ["linear_regression", "logistic_regression", "decision_tree", "random_forest", "svm", "neural_network"]
        elif ml_type == "unsupervised":
            algorithms = ["k_means", "hierarchical_clustering", "pca", "dbscan", "gaussian_mixture"]
        else:
            algorithms = ["q_learning", "policy_gradient", "actor_critic", "dqn"]
        
        algorithm = random.choice(algorithms)
        
        return {
            "task_id": f"ml_{task_id:06d}",
            "type": "machine_learning",
            "difficulty": difficulty,
            "ml_type": ml_type,
            "algorithm": algorithm,
            "problem_statement": f"Implement {algorithm.replace('_', ' ')} for {ml_type} learning",
            "dataset_requirements": self._generate_ml_dataset_requirements(ml_type),
            "implementation_steps": self._generate_ml_steps(algorithm),
            "evaluation_metrics": self._generate_ml_metrics(ml_type),
            "hyperparameters": self._generate_hyperparameters(algorithm),
            "tags": ["machine_learning", ml_type, algorithm],
            "created_at": datetime.datetime.now().isoformat(),
            "estimated_time_minutes": int(difficulty * 300 + 90)
        }
    
    def generate_tables_data(self, format_type: str = "csv") -> List[str]:
        """توليد بيانات الجداول"""
        output_files = []
        
        # جدول الخوارزميات
        algorithms_data = []
        for i in range(100):
            algorithms_data.append({
                "id": i + 1,
                "name": f"{random.choice(self.algorithms_types)} Algorithm {i+1}",
                "type": random.choice(self.algorithms_types),
                "time_complexity": random.choice(["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(2^n)"]),
                "space_complexity": random.choice(["O(1)", "O(log n)", "O(n)", "O(n²)"]),
                "difficulty": random.choice(self.difficulty_levels),
                "language": random.choice(self.programming_languages),
                "use_cases": fake.text(max_nb_chars=100),
                "created_date": fake.date_between(start_date='-2y', end_date='today'),
                "success_rate": round(random.uniform(0.6, 0.95), 2),
                "avg_execution_time_ms": random.randint(1, 1000)
            })
        
        algorithms_file = self._save_table_data(algorithms_data, "algorithms", format_type)
        output_files.append(algorithms_file)
        
        # جدول التحديات
        challenges_data = []
        for i in range(200):
            challenges_data.append({
                "challenge_id": f"CH{i+1:04d}",
                "title": fake.sentence(nb_words=4),
                "description": fake.text(max_nb_chars=200),
                "type": random.choice(["algorithm", "web_dev", "data_analysis", "ml"]),
                "difficulty_score": round(random.uniform(0.1, 1.0), 2),
                "estimated_time_hours": random.randint(1, 20),
                "tags": ",".join(random.sample(["python", "javascript", "algorithm", "web", "data", "ml"], 3)),
                "created_by": fake.name(),
                "created_at": fake.date_time_between(start_date='-1y', end_date='now'),
                "attempts": random.randint(0, 500),
                "success_count": random.randint(0, 300),
                "avg_score": round(random.uniform(0.3, 0.9), 2)
            })
        
        challenges_file = self._save_table_data(challenges_data, "challenges", format_type)
        output_files.append(challenges_file)
        
        # جدول الأداء
        performance_data = []
        for i in range(500):
            performance_data.append({
                "session_id": str(uuid.uuid4()),
                "seed_id": f"seed_{random.randint(1, 50):03d}",
                "challenge_id": f"CH{random.randint(1, 200):04d}",
                "start_time": fake.date_time_between(start_date='-6m', end_date='now'),
                "end_time": fake.date_time_between(start_date='-6m', end_date='now'),
                "score": round(random.uniform(0.0, 1.0), 3),
                "execution_time_seconds": random.randint(5, 3600),
                "memory_usage_mb": random.randint(10, 500),
                "lines_of_code": random.randint(10, 200),
                "test_cases_passed": random.randint(0, 20),
                "test_cases_total": random.randint(10, 20),
                "error_count": random.randint(0, 5),
                "warnings_count": random.randint(0, 10),
                "code_quality_score": round(random.uniform(0.5, 1.0), 2)
            })
        
        performance_file = self._save_table_data(performance_data, "performance", format_type)
        output_files.append(performance_file)
        
        return output_files
    
    def _save_table_data(self, data: List[Dict], name: str, format_type: str) -> str:
        """حفظ بيانات الجدول بالصيغة المحددة"""
        if format_type.lower() == "csv":
            output_file = os.path.join(self.output_dir, "tables", f"{name}.csv")
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False, encoding='utf-8')
        elif format_type.lower() == "json":
            output_file = os.path.join(self.output_dir, "tables", f"{name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        elif format_type.lower() == "parquet":
            output_file = os.path.join(self.output_dir, "tables", f"{name}.parquet")
            df = pd.DataFrame(data)
            df.to_parquet(output_file, index=False)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return output_file
    
    # Helper methods للتوليد
    def _get_time_complexity(self, algorithm_type: str) -> str:
        complexity_map = {
            "Sorting": random.choice(["O(n log n)", "O(n²)"]),
            "Searching": random.choice(["O(log n)", "O(n)"]),
            "Graph": random.choice(["O(V + E)", "O(V²)", "O(E log V)"]),
            "Dynamic Programming": "O(n²)",
            "Greedy": "O(n log n)",
            "Divide and Conquer": "O(n log n)",
            "Backtracking": "O(2^n)",
            "Tree Traversal": "O(n)",
            "String Matching": "O(n + m)",
            "Number Theory": "O(√n)",
            "Geometry": "O(n log n)",
            "Machine Learning": "O(n³)"
        }
        return complexity_map.get(algorithm_type, "O(n)")
    
    def _get_space_complexity(self, algorithm_type: str) -> str:
        space_map = {
            "Sorting": random.choice(["O(1)", "O(log n)", "O(n)"]),
            "Searching": "O(1)",
            "Graph": "O(V)",
            "Dynamic Programming": "O(n²)",
            "Greedy": "O(1)",
            "Divide and Conquer": "O(log n)",
            "Backtracking": "O(n)",
            "Tree Traversal": "O(h)",
            "String Matching": "O(m)",
            "Number Theory": "O(1)",
            "Geometry": "O(n)",
            "Machine Learning": "O(n²)"
        }
        return space_map.get(algorithm_type, "O(1)")
    
    def _generate_test_cases(self, algorithm_type: str) -> List[Dict]:
        """توليد حالات اختبار"""
        if algorithm_type == "Sorting":
            return [
                {"input": [3, 1, 4, 1, 5, 9, 2, 6], "expected": [1, 1, 2, 3, 4, 5, 6, 9]},
                {"input": [], "expected": []},
                {"input": [1], "expected": [1]},
                {"input": [5, 4, 3, 2, 1], "expected": [1, 2, 3, 4, 5]}
            ]
        elif algorithm_type == "Searching":
            return [
                {"input": {"arr": [1, 2, 3, 4, 5], "target": 3}, "expected": 2},
                {"input": {"arr": [1, 2, 3, 4, 5], "target": 6}, "expected": -1},
                {"input": {"arr": [], "target": 1}, "expected": -1}
            ]
        else:
            return [
                {"input": "sample_input", "expected": "sample_output"},
                {"input": "edge_case", "expected": "edge_result"}
            ]
    
    def _generate_hints(self, algorithm_type: str) -> List[str]:
        """توليد تلميحات"""
        hints_map = {
            "Sorting": [
                "Consider using divide and conquer approach",
                "Think about the pivot selection strategy",
                "Handle edge cases like empty arrays"
            ],
            "Searching": [
                "Use binary search for sorted arrays",
                "Check array bounds carefully",
                "Consider iterative vs recursive implementation"
            ],
            "Graph": [
                "Choose appropriate graph representation",
                "Consider BFS vs DFS based on the problem",
                "Handle disconnected components"
            ]
        }
        return hints_map.get(algorithm_type, ["Think step by step", "Consider edge cases", "Optimize for time complexity"])
    
    def _generate_web_requirements(self, framework: str, features: List[str]) -> List[str]:
        """توليد متطلبات تطوير الويب"""
        base_requirements = [
            f"Use {framework} framework",
            "Implement responsive design",
            "Follow modern web standards",
            "Include error handling"
        ]
        
        feature_requirements = {
            "user authentication": "Implement secure login/logout functionality",
            "responsive design": "Ensure mobile-first responsive layout",
            "API integration": "Connect to RESTful API endpoints",
            "database operations": "Implement CRUD operations",
            "real-time updates": "Use WebSocket or Server-Sent Events",
            "file upload": "Handle file upload with validation",
            "search functionality": "Implement search with filters",
            "pagination": "Add pagination for large datasets",
            "form validation": "Client and server-side validation"
        }
        
        for feature in features:
            if feature in feature_requirements:
                base_requirements.append(feature_requirements[feature])
        
        return base_requirements
    
    def _generate_web_structure(self, framework: str) -> Dict[str, List[str]]:
        """توليد هيكل مشروع الويب"""
        if framework in ["React", "Vue", "Angular"]:
            return {
                "components": ["Header", "Footer", "Navigation", "MainContent"],
                "pages": ["Home", "About", "Contact", "Dashboard"],
                "services": ["API", "Auth", "Utils"],
                "styles": ["global.css", "components.css", "responsive.css"]
            }
        else:  # Backend frameworks
            return {
                "routes": ["auth", "api", "admin"],
                "models": ["User", "Product", "Order"],
                "services": ["database", "email", "payment"],
                "middleware": ["auth", "cors", "logging"]
            }
    
    def _generate_web_tests(self, features: List[str]) -> List[str]:
        """توليد سيناريوهات اختبار الويب"""
        base_tests = [
            "Test page loading and rendering",
            "Test responsive design on different screen sizes",
            "Test navigation between pages"
        ]
        
        feature_tests = {
            "user authentication": "Test login/logout functionality",
            "API integration": "Test API calls and error handling",
            "form validation": "Test form validation rules",
            "search functionality": "Test search with various queries",
            "file upload": "Test file upload with different file types"
        }
        
        for feature in features:
            if feature in feature_tests:
                base_tests.append(feature_tests[feature])
        
        return base_tests
    
    def _generate_data_description(self, dataset_type: str) -> Dict[str, Any]:
        """توليد وصف البيانات"""
        descriptions = {
            "sales": {
                "columns": ["date", "product_id", "quantity", "price", "customer_id", "region"],
                "size": "10,000 rows",
                "time_range": "2022-2024",
                "format": "CSV"
            },
            "customer": {
                "columns": ["customer_id", "age", "gender", "location", "purchase_history", "preferences"],
                "size": "5,000 rows",
                "time_range": "2023-2024",
                "format": "JSON"
            },
            "financial": {
                "columns": ["date", "symbol", "open", "high", "low", "close", "volume"],
                "size": "50,000 rows",
                "time_range": "2020-2024",
                "format": "CSV"
            }
        }
        return descriptions.get(dataset_type, {"columns": ["id", "value", "timestamp"], "size": "1,000 rows"})
    
    def _generate_analysis_steps(self, analysis_type: str) -> List[str]:
        """توليد خطوات التحليل"""
        steps_map = {
            "descriptive statistics": [
                "Load and explore the dataset",
                "Calculate mean, median, mode",
                "Identify outliers",
                "Generate summary statistics"
            ],
            "correlation analysis": [
                "Load the dataset",
                "Calculate correlation matrix",
                "Visualize correlations",
                "Interpret results"
            ],
            "clustering": [
                "Preprocess the data",
                "Choose optimal number of clusters",
                "Apply clustering algorithm",
                "Evaluate cluster quality"
            ]
        }
        return steps_map.get(analysis_type, ["Load data", "Analyze", "Visualize", "Report"])
    
    def _generate_expected_outputs(self, analysis_type: str) -> List[str]:
        """توليد المخرجات المتوقعة"""
        outputs_map = {
            "descriptive statistics": [
                "Summary statistics table",
                "Distribution plots",
                "Outlier detection report"
            ],
            "correlation analysis": [
                "Correlation matrix",
                "Heatmap visualization",
                "Correlation insights"
            ],
            "clustering": [
                "Cluster assignments",
                "Cluster visualization",
                "Cluster characteristics"
            ]
        }
        return outputs_map.get(analysis_type, ["Analysis report", "Visualizations"])
    
    def _generate_ml_dataset_requirements(self, ml_type: str) -> Dict[str, Any]:
        """توليد متطلبات بيانات التعلم الآلة"""
        if ml_type == "supervised":
            return {
                "features": random.randint(5, 20),
                "samples": random.randint(1000, 10000),
                "target_type": random.choice(["classification", "regression"]),
                "missing_values": "handle appropriately",
                "scaling": "required"
            }
        elif ml_type == "unsupervised":
            return {
                "features": random.randint(3, 15),
                "samples": random.randint(500, 5000),
                "preprocessing": "normalization required",
                "dimensionality": "consider reduction"
            }
        else:  # reinforcement
            return {
                "environment": "define state and action spaces",
                "reward_function": "design appropriate rewards",
                "episodes": random.randint(1000, 10000),
                "exploration": "balance exploration vs exploitation"
            }
    
    def _generate_ml_steps(self, algorithm: str) -> List[str]:
        """توليد خطوات التعلم الآلة"""
        common_steps = [
            "Load and preprocess data",
            "Split data into train/validation/test sets",
            "Train the model",
            "Evaluate performance",
            "Tune hyperparameters",
            "Generate final predictions"
        ]
        
        algorithm_specific = {
            "neural_network": ["Design network architecture", "Choose activation functions"],
            "random_forest": ["Set number of trees", "Configure tree depth"],
            "svm": ["Choose kernel function", "Set regularization parameter"],
            "k_means": ["Choose number of clusters", "Initialize centroids"],
            "q_learning": ["Define Q-table", "Set learning rate and discount factor"]
        }
        
        if algorithm in algorithm_specific:
            return common_steps[:2] + algorithm_specific[algorithm] + common_steps[2:]
        
        return common_steps
    
    def _generate_ml_metrics(self, ml_type: str) -> List[str]:
        """توليد مقاييس التقييم"""
        if ml_type == "supervised":
            return ["accuracy", "precision", "recall", "f1_score", "confusion_matrix"]
        elif ml_type == "unsupervised":
            return ["silhouette_score", "inertia", "calinski_harabasz_score"]
        else:  # reinforcement
            return ["cumulative_reward", "episode_length", "convergence_rate"]
    
    def _generate_hyperparameters(self, algorithm: str) -> Dict[str, Any]:
        """توليد المعاملات الفائقة"""
        hyperparams_map = {
            "linear_regression": {"fit_intercept": True, "normalize": False},
            "random_forest": {"n_estimators": 100, "max_depth": None, "min_samples_split": 2},
            "svm": {"C": 1.0, "kernel": "rbf", "gamma": "scale"},
            "neural_network": {"hidden_layers": [100, 50], "learning_rate": 0.001, "epochs": 100},
            "k_means": {"n_clusters": 3, "init": "k-means++", "max_iter": 300},
            "q_learning": {"learning_rate": 0.1, "discount_factor": 0.95, "epsilon": 0.1}
        }
        return hyperparams_map.get(algorithm, {"parameter": "value"})

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="Generate training data for AI Seed")
    parser.add_argument("--type", choices=["all", "jsonl", "tables"], default="all",
                       help="Type of data to generate")
    parser.add_argument("--count", type=int, default=1000,
                       help="Number of items to generate")
    parser.add_argument("--format", choices=["csv", "json", "parquet"], default="csv",
                       help="Format for table data")
    parser.add_argument("--output", default="data",
                       help="Output directory")
    
    args = parser.parse_args()
    
    generator = DataGenerator(args.output)
    
    print(f"🚀 Starting data generation...")
    print(f"📁 Output directory: {args.output}")
    
    if args.type in ["all", "jsonl"]:
        print(f"📝 Generating JSONL training data ({args.count} items)...")
        jsonl_file = generator.generate_jsonl_training_data(args.count)
        print(f"✅ JSONL data saved to: {jsonl_file}")
    
    if args.type in ["all", "tables"]:
        print(f"📊 Generating table data ({args.format} format)...")
        table_files = generator.generate_tables_data(args.format)
        for file in table_files:
            print(f"✅ Table data saved to: {file}")
    
    print("🎉 Data generation completed!")

if __name__ == "__main__":
    main()

