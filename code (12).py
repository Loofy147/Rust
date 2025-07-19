import asyncio
import os
import logging
import time
import json
import re
from typing import Dict, List, Any
from datetime import datetime
import shutil
import uuid

# ==============================================================================
# 1. FOUNDATIONAL CLASSES (Unaltered)
# ==============================================================================

class Agent:
    def __init__(self, name="BaseAgent", message_bus=None, config=None):
        self.name = name
        self.inbox = []
        self.config = config if config is not None else {}
        self.state = "waiting_for_task"
        self.message_bus = message_bus

    def send(self, message, target_agent_name=None):
        if self.message_bus:
            asyncio.create_task(self.message_bus.publish(message, target=target_agent_name))
        else:
            print(f"Agent '{self.name}' Warning: Message bus not configured.")

    async def run(self):
        try:
            while True:
                if self.inbox:
                     msg = self.inbox.pop(0)
                     await self.handle_message(msg)
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            self.state = "stopped"

    async def handle_message(self, msg):
        print(f"Agent '{self.name}' unhandled message: {msg}")


class CentralMessageBus:
    def __init__(self):
        self._agent_inboxes = {}
        self._subscriptions = {}

    def register_agent(self, agent_name, inbox_ref):
        self._agent_inboxes[agent_name] = inbox_ref

    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]:
            self._subscriptions[event_type].append(agent)

    async def publish(self, message, target=None):
        if target:
            if target in self._agent_inboxes:
                self._agent_inboxes[target].append(message)
        else:
            event_type = message.get('type')
            if event_type in self._subscriptions:
                for agent in self._subscriptions.get(event_type, []):
                    agent.inbox.append(message)


class ArchitectureEventType:
    STRUCTURED_DATA = "structured_data"
    TRAINING_TASK_CREATED = "training_task_created" # New event for enriched data


# ==============================================================================
# 2. CORE DATA AGENTS (DataCreator is unchanged)
# ==============================================================================
class DataCreatorAgent(Agent):
    """(Code from previous step - loads and publishes curated real data)"""
    async def handle_message(self, msg):
        # Simplified for demonstration
        if msg.get("type") == "publish_curated_data":
            print("DataCreatorAgent: Publishing curated data...")
            self.send({"type": ArchitectureEventType.STRUCTURED_DATA, "category": "algorithms", "data": self._get_algorithm_implementations()})
            self.send({"type": ArchitectureEventType.STRUCTURED_DATA, "category": "challenges", "data": self._get_coding_challenges()})
    def _get_algorithm_implementations(self) -> List[Dict[str, Any]]:
        return [{'name': 'Quick Sort', 'type': 'Sorting', 'time_complexity': 'O(n log n) average, O(n²) worst', 'description': 'Implement an efficient Quick Sort algorithm.', 'implementation': 'def quicksort(arr):...', 'source': 'algorithm_collection'}, {'name': 'Binary Search', 'type': 'Searching', 'time_complexity': 'O(log n)', 'description': 'Implement Binary Search on a sorted array.', 'implementation': 'def binary_search(arr, target):...', 'source': 'algorithm_collection'}]
    def _get_coding_challenges(self) -> List[Dict[str, Any]]:
        return [{'id': 'two_sum', 'title': 'Two Sum', 'difficulty': 'Easy', 'category': 'Array', 'problem_statement': 'Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.', 'solution': 'def two_sum(nums, target):...', 'source': 'leetcode_style'}]

# ==============================================================================
# 3. NEW AND IMPROVED AGENTS (The core of this improvement)
# ==============================================================================

class EnrichmentAgent(Agent):
    """
    Replaces Faker-based generation. It consumes real data and enriches
    it into a structured training task format.
    """
    def __init__(self, name="EnrichmentAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        if self.message_bus:
            # Subscribes to the basic structured data from the DataCreator
            self.message_bus.subscribe(ArchitectureEventType.STRUCTURED_DATA, self)
            print(f"EnrichmentAgent '{self.name}' is online and ready to build knowledge.")

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.STRUCTURED_DATA:
            print(f"EnrichmentAgent: Received {len(msg.get('data',[]))} items for enrichment.")
            for item in msg.get("data", []):
                # The logic to transform basic data into a rich task
                enriched_task = self._create_training_task(item)
                # Publish the new, enriched data for another agent to save
                self.send({
                    "type": ArchitectureEventType.TRAINING_TASK_CREATED,
                    "task": enriched_task
                })

    def _create_training_task(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a piece of structured data into a detailed training task.
        This function contains the "intelligence" to build the training sample.
        """
        source_category = item.get('source', 'unknown')
        task_id = f"task_{source_category}_{uuid.uuid4().hex[:8]}"

        # Base structure from your `data_generator.py` schema
        task = {
            "task_id": task_id,
            "type": item.get('category', 'generic'),
            "difficulty_level": item.get('difficulty', 'Intermediate'), # Default difficulty
            "problem_statement": item.get('problem_statement') or item.get('description', 'No description provided.'),
            "solution_code": item.get('solution') or item.get('implementation', '# No code provided'),
            "metadata": {
                "source": item.get('source'),
                "title": item.get('name') or item.get('title'),
                "collected_at": item.get('collected_at', datetime.now().isoformat()),
            },
            "tags": self._extract_tags(item),
            "created_at": datetime.now().isoformat()
        }

        # Add specific fields based on item type
        if task['type'] == 'algorithms':
            task['metadata']['time_complexity'] = item.get('time_complexity')
            task['metadata']['space_complexity'] = item.get('space_complexity')
        
        # This is where real test case generation/extraction would happen.
        # For now, we'll add placeholder test cases.
        task['validation'] = {
            "test_cases": self._generate_test_cases(item)
        }
        
        return task

    def _extract_tags(self, item: Dict[str, Any]) -> List[str]:
        """Extracts relevant tags from the data item."""
        tags = set()
        if item.get('category'): tags.add(item['category'])
        if item.get('type'): tags.add(item['type'])
        if item.get('difficulty'): tags.add(item['difficulty'].lower())
        tags.update(item.get('topics', []))
        return list(tags)

    def _generate_test_cases(self, item: Dict[str, Any]) -> List[Dict]:
        """
        Placeholder for a sophisticated test case generator.
        In a real scenario, this would involve static analysis or parsing example code.
        """
        if item.get('id') == 'two_sum':
            return [
                {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected_output": "[0, 1]"},
                {"input": {"nums": [3, 2, 4], "target": 6}, "expected_output": "[1, 2]"}
            ]
        if item.get('name') == 'Quick Sort':
            return [
                {"input": {"arr": [3, 1, 4, 1, 5, 9]}, "expected_output": "[1, 1, 3, 4, 5, 9]"},
                {"input": {"arr": []}, "expected_output": "[]"}
            ]
        return [{"input": "generic_input", "expected_output": "generic_output"}]


class PersistenceAgent(Agent):
    """
    The Archivist, now upgraded to handle different types of data,
    including the new enriched training tasks.
    """
    def __init__(self, name="PersistenceAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        self.output_dir = config.get("output_dir", "./final_training_data")
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

        if self.message_bus:
            # Now listens for BOTH basic and enriched data events
            self.message_bus.subscribe(ArchitectureEventType.STRUCTURED_DATA, self)
            self.message_bus.subscribe(ArchitectureEventType.TRAINING_TASK_CREATED, self)
            print(f"PersistenceAgent '{self.name}' is online and archiving multiple data types.")

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.STRUCTURED_DATA:
            # We can still save the original, "raw" structured data if needed
            await self.save_data_json(msg)
        elif msg.get("type") == ArchitectureEventType.TRAINING_TASK_CREATED:
            # This handles the new, enriched tasks, saving them as JSONL
            await self.save_data_jsonl(msg)

    async def save_data_json(self, msg: Dict[str, Any]):
        """Saves batches of structured data to a single JSON file."""
        category = msg.get("category", "structured")
        target_dir = os.path.join(self.output_dir, "structured", category)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, "data.json")
        print(f"PersistenceAgent: Archiving {len(msg.get('data',[]))} structured items to '{file_path}'")
        with open(file_path, 'a', encoding='utf-8') as f:
            for item in msg.get('data', []):
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

    async def save_data_jsonl(self, msg: Dict[str, Any]):
        """Saves enriched training tasks to a JSONL file, ideal for training."""
        target_dir = os.path.join(self.output_dir, "training_tasks")
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, "tasks.jsonl")
        print(f"PersistenceAgent: Archiving enriched task to '{file_path}'")
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(msg.get('task'), ensure_ascii=False) + '\n')


# ==============================================================================
# 4. DEMONSTRATION ORCHESTRATOR
# ==============================================================================

async def main():
    print("--- Orchestration Starting: Enrichment Pipeline ---")
    bus = CentralMessageBus()
    
    # Initialize all agents in the pipeline
    data_creator = DataCreatorAgent(name="DataCreatorAgent", message_bus=bus)
    enrichment_agent = EnrichmentAgent(name="EnrichmentAgent", message_bus=bus)
    persistence_agent = PersistenceAgent(name="PersistenceAgent", message_bus=bus)

    # Register agents
    for agent in [data_creator, enrichment_agent, persistence_agent]:
        bus.register_agent(agent.name, agent.inbox)
    
    # Start agent background tasks
    agent_tasks = [
        asyncio.create_task(agent.run()) for agent in [data_creator, enrichment_agent, persistence_agent]
    ]

    print("\n--- Triggering the Data Pipeline ---\n")
    # A single command starts the entire cascade: Create -> Enrich -> Persist
    data_creator.send({"type": "publish_curated_data"})
    
    await asyncio.sleep(1) # Allow pipeline to complete

    print("\n--- Final Data Product ---")
    output_base_dir = persistence_agent.output_dir
    print(f"Contents of '{output_base_dir}':")
    for root, _, files in os.walk(output_base_dir):
        for f in files:
            path = os.path.join(root, f)
            print(f"\n📄 FILE: {os.path.relpath(path, output_base_dir)}")
            print("-" * 20)
            with open(path, 'r', encoding='utf-8') as fin:
                for line in fin:
                    print(line.strip())

    # Shutdown
    print("\n--- Shutting down agents ---")
    for task in agent_tasks: task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    print("--- Orchestration Finished ---")

if __name__ == "__main__":
    asyncio.run(main())