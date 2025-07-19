import asyncio
import os
import logging
import time
import json
import re
import fnmatch
from typing import Dict, List, Any
from datetime import datetime
import shutil

# ==============================================================================
# 1. FOUNDATIONAL CLASSES (With corrected state management)
# ==============================================================================

class Agent:
    def __init__(self, name="BaseAgent", message_bus=None, config=None):
        self.name = name
        self.inbox = []
        self.config = config if config is not None else {}
        # The agent starts as idle/waiting, not immediately "running"
        self.state = "waiting_for_task"
        self.message_bus = message_bus

    def send(self, message, target_agent_name=None):
        if self.message_bus:
            # Send message via the bus without blocking the agent
            asyncio.create_task(self.message_bus.publish(message, target=target_agent_name))
        else:
            print(f"Agent '{self.name}' Warning: Message bus not configured.")

    async def run(self):
        # **FIX**: Removed `self.state = "running"` from here.
        # The state should describe the task status, not the run loop status.
        try:
            while True:
                if self.inbox:
                     msg = self.inbox.pop(0)
                     await self.handle_message(msg)
                await asyncio.sleep(0.05) # A short sleep to yield control
        except asyncio.CancelledError:
            self.state = "stopped"
            # print(f"Agent '{self.name}' run loop cancelled.") # Verbose, can be enabled for debug

    async def handle_message(self, msg):
        print(f"Agent '{self.name}' received a message but has no specific handler logic. Message: {msg}")


class CentralMessageBus:
    def __init__(self):
        self._agent_inboxes = {}
        self._subscriptions = {}

    def register_agent(self, agent_name, inbox_ref):
        self._agent_inboxes[agent_name] = inbox_ref
        print(f"Message Bus: Agent '{agent_name}' registered.")

    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]:
            self._subscriptions[event_type].append(agent)
            print(f"Message Bus: Agent '{agent.name}' subscribed to '{event_type}'.")

    async def publish(self, message, target=None):
        # Logic for Direct Message
        if target:
            if target in self._agent_inboxes:
                self._agent_inboxes[target].append(message)
            else:
                print(f"Message Bus Warning: Target agent '{target}' not found.")
        # Logic for Publish/Subscribe Event
        else:
            event_type = message.get('type')
            if event_type in self._subscriptions:
                for agent in self._subscriptions[event_type]:
                    agent.inbox.append(message)


class ArchitectureEventType:
    REPO_DATA_EXTRACTED = "repo_data_extracted"
    STRUCTURED_DATA = "structured_data"


# ==============================================================================
# 2. NEW AND UPGRADED AGENTS (With robust state checking)
# ==============================================================================

class DataCreatorAgent(Agent):
    def __init__(self, name="DataCreatorAgent", message_bus=None, config=None):
        super().__init__(name=name, message_bus=message_bus, config=config)
        if self.message_bus:
            self.message_bus.subscribe("publish_curated_data", self)
            print(f"DataCreatorAgent '{self.name}' is online and subscribed to tasks.")

    async def handle_message(self, msg):
        msg_type = msg.get("type")

        # This state check is now effective and correct.
        if self.state != "waiting_for_task":
            print(f"DataCreatorAgent is busy processing another task. Ignoring message: {msg_type}")
            return

        print(f"DataCreatorAgent received task: '{msg_type}'. Changing state to 'processing_task'.")
        self.state = "processing_task"
        try:
            if msg_type == "publish_curated_data":
                await self.publish_curated_data()
        except Exception as e:
            print(f"DataCreatorAgent Error processing {msg_type}: {e}")
        finally:
            # Ensure the agent is ready for a new task after finishing.
            self.state = "waiting_for_task"
            print(f"DataCreatorAgent finished task: '{msg_type}'. State reset to 'waiting_for_task'.")

    async def publish_curated_data(self):
        print("DataCreatorAgent: Loading and publishing curated data knowledge base.")
        
        # Publish Algorithm Implementations
        algorithms_data = self._get_algorithm_implementations()
        self.send({
            "type": ArchitectureEventType.STRUCTURED_DATA,
            "category": "algorithms",
            "source": "curated_knowledge_base",
            "data": algorithms_data
        })
        print(f"-> Published {len(algorithms_data)} curated algorithm items.")

        # Publish Coding Challenges
        challenges_data = self._get_coding_challenges()
        self.send({
            "type": ArchitectureEventType.STRUCTURED_DATA,
            "category": "challenges",
            "source": "curated_knowledge_base",
            "data": challenges_data
        })
        print(f"-> Published {len(challenges_data)} curated challenge items.")

        # Publish Documentation
        docs_data = self._get_documentation_and_tutorials()
        self.send({
            "type": ArchitectureEventType.STRUCTURED_DATA,
            "category": "documentation",
            "source": "curated_knowledge_base",
            "data": docs_data
        })
        print(f"-> Published {len(docs_data)} curated documentation items.")
    
    # --- Data Definitions from real_data_collector.py ---
    def _get_algorithm_implementations(self) -> List[Dict[str, Any]]:
        return [{'name': 'Quick Sort', 'type': 'Sorting', 'time_complexity': 'O(n log n) average, O(n²) worst', 'space_complexity': 'O(log n)', 'description': 'Divide-and-conquer sorting algorithm', 'implementation': 'def quicksort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)', 'use_cases': ['General purpose sorting', 'In-place sorting when memory is limited'], 'source': 'algorithm_collection', 'collected_at': datetime.now().isoformat()}, {'name': 'Merge Sort', 'type': 'Sorting', 'time_complexity': 'O(n log n)', 'space_complexity': 'O(n)', 'description': 'Stable divide-and-conquer sorting algorithm', 'implementation': 'def mergesort(arr):\n    if len(arr) <= 1: return arr\n    mid = len(arr) // 2\n    left = mergesort(arr[:mid])\n    right = mergesort(arr[mid:])\n    # ... (merge logic)', 'use_cases': ['When stability is required', 'External sorting'], 'source': 'algorithm_collection', 'collected_at': datetime.now().isoformat()}]
    def _get_coding_challenges(self) -> List[Dict[str, Any]]:
        return [{'id': 'two_sum', 'title': 'Two Sum', 'difficulty': 'Easy', 'category': 'Array', 'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.', 'solution': 'def two_sum_optimized(nums, target):\n    num_map = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in num_map:\n            return [num_map[complement], i]\n        num_map[num] = i\n    return []', 'topics': ['Array', 'Hash Table'], 'companies': ['Amazon', 'Google', 'Facebook', 'Microsoft'], 'source': 'leetcode_style', 'collected_at': datetime.now().isoformat()}]
    def _get_documentation_and_tutorials(self) -> List[Dict[str, Any]]:
        return [{'title': 'Understanding Time and Space Complexity', 'category': 'Algorithms', 'level': 'Beginner', 'content': '# Understanding Time and Space Complexity\n\n## What is Time Complexity?\nTime complexity is a way to describe how the runtime of an algorithm changes as the input size grows.', 'topics': ['Algorithms', 'Complexity Analysis', 'Big O'], 'estimated_reading_time': '15 minutes', 'source': 'educational_content', 'collected_at': datetime.now().isoformat()}]


class PersistenceAgent(Agent):
    def __init__(self, name="PersistenceAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        self.output_dir = self.config.get("output_dir", "./unified_orchestrator/data/real_data")
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)
        
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.STRUCTURED_DATA, self)
            print(f"PersistenceAgent '{self.name}' is online and subscribed to structured data.")

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.STRUCTURED_DATA:
            await self.save_data(msg)

    async def save_data(self, msg: Dict[str, Any]):
        category = msg.get("category", "uncategorized")
        data = msg.get("data", [])
        
        category_dir = os.path.join(self.output_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        source = msg.get("source", "generic").replace(" ", "_")
        file_name = f"{source}.json"
        output_path = os.path.join(category_dir, file_name)
        
        print(f"PersistenceAgent: Received {len(data)} items. Writing to '{output_path}'")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ==============================================================================
# 3. DEMONSTRATION ORCHESTRATOR
# ==============================================================================

async def main():
    print("--- Orchestration Starting: From Script to Agent Ecosystem ---")
    bus = CentralMessageBus()
    
    # Initialize agents
    data_creator = DataCreatorAgent(name="DataCreatorAgent", message_bus=bus)
    persistence_agent = PersistenceAgent(name="PersistenceAgent", message_bus=bus)

    # Register agents with the bus
    bus.register_agent(data_creator.name, data_creator.inbox)
    bus.register_agent(persistence_agent.name, persistence_agent.inbox)
    
    # Start agent background tasks
    agent_tasks = [
        asyncio.create_task(data_creator.run()),
        asyncio.create_task(persistence_agent.run())
    ]

    print("\n--- Sending command to publish curated knowledge base ---")
    # The Orchestrator (this main function) sends a single command...
    data_creator.send({"type": "publish_curated_data"})
    
    # Allow time for the event to propagate through the system
    await asyncio.sleep(1)

    print("\n--- System state after processing ---")
    output_base_dir = persistence_agent.output_dir
    if os.path.exists(output_base_dir):
        print(f"Contents of '{output_base_dir}':")
        # Walk through the directory and print the structure
        for root, dirs, files in os.walk(output_base_dir):
            level = root.replace(output_base_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                print(f'{sub_indent}{f}')
    else:
        print("Output directory not created.")
        
    # Cleanly shut down agents
    print("\n--- Shutting down agents ---")
    for task in agent_tasks:
        task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    
    print("\n--- Orchestration Finished ---")

if __name__ == "__main__":
    asyncio.run(main())