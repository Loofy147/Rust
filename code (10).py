#!/usr/bin/env python3
"""
Training Data Formatter for AI Seed
===================================

This script transforms raw, real data collected by 'real_data_collector.py'
into a structured JSONL format suitable for training the AI seed.

It replaces the previous 'DataGenerator' by grounding the training data
in real-world examples instead of synthetic ones.
"""

import os
import json
import datetime
import argparse
from typing import Dict, List, Any

class TrainingDataFormatter:
    """
    Reads collected real data and formats it into structured training examples.
    """
    def __init__(self, input_dir: str = "data/real_data", output_dir: str = "data/training_data"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def format_all_sources(self) -> str:
        """
        Processes all available real data sources and generates a unified
        JSONL training file.
        """
        output_file = os.path.join(self.output_dir, "training_data.jsonl")
        print(f"💎 Formatting real data into {output_file}...")

        all_tasks = []

        # Process algorithms
        algo_file = os.path.join(self.input_dir, "algorithms", "implementations.json")
        if os.path.exists(algo_file):
            with open(algo_file, 'r', encoding='utf-8') as f:
                algorithms = json.load(f)
            for algo_record in algorithms:
                all_tasks.append(self._format_algorithm_as_task(algo_record))
            print(f"   -> Processed {len(algorithms)} algorithms.")
        else:
            print(f"   ⚠️  Algorithm file not found: {algo_file}")

        # Process challenges
        challenge_file = os.path.join(self.input_dir, "challenges", "coding_challenges.json")
        if os.path.exists(challenge_file):
            with open(challenge_file, 'r', encoding='utf-8') as f:
                challenges = json.load(f)
            for challenge_record in challenges:
                all_tasks.append(self._format_challenge_as_task(challenge_record))
            print(f"   -> Processed {len(challenges)} challenges.")
        else:
            print(f"   ⚠️  Challenge file not found: {challenge_file}")
            
        # Write to JSONL file
        with open(output_file, 'w', encoding='utf-8') as f:
            for task in all_tasks:
                f.write(json.dumps(task, ensure_ascii=False) + '\n')

        print(f"✅ Successfully formatted {len(all_tasks)} records.")
        return output_file

    def _format_algorithm_as_task(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Converts a real algorithm record into a structured training task."""
        return {
            "task_id": f"algo_{record.get('name', 'untitled').lower().replace(' ', '_')}",
            "type": "algorithm_implementation",
            "source": record.get("source", "unknown"),
            "problem_statement": f"Implement the {record.get('name', 'N/A')} algorithm, which is a {record.get('type', 'N/A')} algorithm.",
            "context": {
                "description": record.get("description", ""),
                "time_complexity": record.get("time_complexity", "N/A"),
                "space_complexity": record.get("space_complexity", "N/A"),
            },
            "solution": {
                "language": "Python", # Assuming Python from collector
                "code": record.get("implementation", "# No implementation provided.")
            },
            "tags": ["algorithm", record.get("type", "untagged").lower()],
            "created_at": datetime.datetime.now().isoformat()
        }

    def _format_challenge_as_task(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Converts a real coding challenge record into a structured training task."""
        return {
            "task_id": f"challenge_{record.get('id', 'untitled')}",
            "type": "problem_solving",
            "source": record.get("source", "unknown"),
            "problem_statement": record.get("description", "No description provided."),
            "context": {
                "title": record.get("title", "Untitled Challenge"),
                "difficulty": record.get("difficulty", "N/A"),
                "category": record.get("category", "N/A"),
                "topics": record.get("topics", [])
            },
            "solution": {
                "language": "Python", # Assuming Python from collector
                "code": record.get("solution", "# No solution provided.")
            },
            "tags": ["challenge", record.get("category", "untagged").lower()] + [t.lower() for t in record.get("topics", [])],
            "created_at": datetime.datetime.now().isoformat()
        }

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Transforms real collected data into structured training JSONL.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # The arguments are simplified as the script's purpose is now more focused.
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/real_data",
        help="Directory where the raw data from the collector is stored."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/training_data",
        help="Directory to save the formatted training_data.jsonl file."
    )
    
    args = parser.parse_args()
    
    formatter = TrainingDataFormatter(input_dir=args.input_dir, output_dir=args.output_dir)
    formatter.format_all_sources()

    # Let's also print the content of the generated file to verify
    print("\n--- Generated training_data.jsonl content ---")
    output_path = os.path.join(args.output_dir, "training_data.jsonl")
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                print(line.strip())
    else:
        print("File not generated.")


if __name__ == "__main__":
    main()
