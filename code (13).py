import asyncio
import os
import logging
import time
import json
import re
import shutil
import uuid
import subprocess
import requests # Needed for the DiscoveryAgent
import fnmatch # Needed for file extraction

# ==============================================================================
# 1. FOUNDATIONAL CLASSES (Unaltered, robust base)
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

    def register_agent(self, agent_name, inbox_ref): self._agent_inboxes[agent_name] = inbox_ref
    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions: self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]: self._subscriptions[event_type].append(agent)

    async def publish(self, message, target=None):
        if target:
            if target in self._agent_inboxes: self._agent_inboxes[target].append(message)
        else:
            event_type = message.get('type')
            for agent in self._subscriptions.get(event_type, []): agent.inbox.append(message)

class ArchitectureEventType:
    STRUCTURED_DATA = "structured_data"
    TRAINING_TASK_CREATED = "training_task_created"
    REPO_DATA_EXTRACTED = "repo_data_extracted" # Raw data from a cloned repo
    # --- Tasking Messages ---
    DISCOVER_NEW_DATA = "discover_new_data"
    CLONE_AND_EXTRACT_REPO = "clone_and_extract_repo"
    PUBLISH_CURATED_DATA = "publish_curated_data"

# ==============================================================================
# 2. THE AUTONOMOUS AGENT PIPELINE
# ==============================================================================

class DiscoveryAgent(Agent):
    """Our autonomous scout for finding new data sources."""
    def __init__(self, name="DiscoveryAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.topics = config.get("topics", ["python-algorithms", "python-data-structures", "machine-learning-from-scratch"])
        self.limit_per_topic = config.get("limit_per_topic", 2)
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.DISCOVER_NEW_DATA, self)

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.DISCOVER_NEW_DATA:
            print("DiscoveryAgent: Received task to discover new data. Starting search.")
            await self.discover_repositories()

    async def discover_repositories(self):
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.github_token: headers['Authorization'] = f'token {self.github_token}'
        
        for topic in self.topics:
            print(f"DiscoveryAgent: Searching GitHub for topic '{topic}'...")
            params = {'q': f'topic:{topic}', 'sort': 'stars', 'order': 'desc', 'per_page': self.limit_per_topic}
            try:
                # Use asyncio.to_thread to avoid blocking the event loop with a network request
                response = await asyncio.to_thread(requests.get, "https://api.github.com/search/repositories", params=params, headers=headers)
                response.raise_for_status()
                repos = response.json().get('items', [])
                print(f"DiscoveryAgent: Found {len(repos)} repositories for '{topic}'.")
                for repo in repos:
                    # DELEGATE the task of cloning to the DataCreatorAgent
                    self.send({
                        "type": ArchitectureEventType.CLONE_AND_EXTRACT_REPO,
                        "repo_url": repo['clone_url'],
                        "source_info": {"name": repo['full_name'], "stars": repo['stargazers_count'], "description": repo.get('description')}
                    })
            except Exception as e:
                print(f"DiscoveryAgent: Error searching for topic {topic}: {e}")
            await asyncio.sleep(1) # Be respectful to the API

class DataCreatorAgent(Agent):
    """Upgraded to handle both dynamic cloning and publishing curated data."""
    def __init__(self, name="DataCreatorAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        self.clone_dir = config.get("clone_dir", "./temp_repos")
        self._processed_repos = set()
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.PUBLISH_CURATED_DATA, self)
            self.message_bus.subscribe(ArchitectureEventType.CLONE_AND_EXTRACT_REPO, self)

    async def handle_message(self, msg):
        msg_type = msg.get("type")
        if self.state != "waiting_for_task": return

        self.state = "processing_task"
        try:
            if msg_type == ArchitectureEventType.PUBLISH_CURATED_DATA:
                await self.publish_curated_data()
            elif msg_type == ArchitectureEventType.CLONE_AND_EXTRACT_REPO:
                await self.process_repo_clone_and_extract(msg)
        finally:
            self.state = "waiting_for_task"
    
    async def process_repo_clone_and_extract(self, msg):
        repo_url = msg.get("repo_url")
        if not repo_url or repo_url in self._processed_repos: return
        self._processed_repos.add(repo_url)
        
        print(f"DataCreatorAgent: Cloning '{repo_url}'...")
        repo_name = msg.get("source_info", {}).get("name", repo_url.split('/')[-1]).replace('/', '_')
        local_path = os.path.join(self.clone_dir, repo_name)
        
        try:
            # Asynchronous cloning process
            process = await asyncio.create_subprocess_exec('git', 'clone', '--depth', '1', repo_url, local_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = await process.communicate()
            if process.returncode != 0: raise Exception(f"Git clone failed: {stderr.decode()}")

            # Extract data
            extracted_files = self._extract_files(local_path)
            # Publish raw file data for the EnrichmentAgent
            self.send({
                "type": ArchitectureEventType.REPO_DATA_EXTRACTED,
                "files": extracted_files,
                "source_info": msg.get("source_info")
            })
        except Exception as e:
            print(f"DataCreatorAgent: Error processing repo {repo_url}: {e}")
        finally:
            if os.path.exists(local_path): shutil.rmtree(local_path)

    def _extract_files(self, repo_path, include_patterns=['*.py', '*.md']):
        extracted = []
        for root, _, files in os.walk(repo_path):
            if '.git' in root: continue
            for filename in files:
                if any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns):
                    try:
                        with open(os.path.join(root, filename), 'r', encoding='utf-8') as f:
                            content = f.read()
                        extracted.append({'path': os.path.relpath(os.path.join(root, filename), repo_path), 'content': content})
                    except: continue # Ignore read errors for simplicity
        return extracted
    
    async def publish_curated_data(self):
        # (Same as previous step, publishes high-quality static data)
        self.send({"type": ArchitectureEventType.STRUCTURED_DATA, "category": "algorithms", "data": self._get_algorithm_implementations()})
    def _get_algorithm_implementations(self): return [{'name': 'Quick Sort', 'type': 'Sorting', 'description': 'Implement Quick Sort.', 'implementation': 'def quicksort(arr):...', 'source': 'curated'}]


class EnrichmentAgent(Agent):
    """Upgraded to enrich both curated data and raw file data."""
    def __init__(self, name="EnrichmentAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.STRUCTURED_DATA, self)
            self.message_bus.subscribe(ArchitectureEventType.REPO_DATA_EXTRACTED, self)

    async def handle_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == ArchitectureEventType.STRUCTURED_DATA:
            print(f"EnrichmentAgent: Enriching {len(msg.get('data',[]))} curated items.")
            for item in msg.get('data', []):
                self.send({"type": ArchitectureEventType.TRAINING_TASK_CREATED, "task": self._create_task_from_structured(item)})
        elif msg_type == ArchitectureEventType.REPO_DATA_EXTRACTED:
            print(f"EnrichmentAgent: Enriching {len(msg.get('files',[]))} raw files.")
            for file_item in msg.get('files', []):
                self.send({"type": ArchitectureEventType.TRAINING_TASK_CREATED, "task": self._create_task_from_raw(file_item, msg.get("source_info"))})

    def _create_task_from_structured(self, item):
        return {"task_id": f"structured_{uuid.uuid4().hex[:8]}", "type": "algorithm", "problem_statement": item.get('description'), "solution_code": item.get('implementation'), "metadata": {"source": item.get('source'), "title": item.get('name')}, "tags": [item.get('type')]}
    
    def _create_task_from_raw(self, file_item, source_info):
        # This is where sophisticated logic would go to parse the raw file content.
        # For now, we'll create a generic task.
        return {"task_id": f"raw_{uuid.uuid4().hex[:8]}", "type": "code_analysis", "problem_statement": f"Analyze the following code from file: {file_item.get('path')}", "solution_code": file_item.get('content'), "metadata": {"source": source_info.get('name') if source_info else 'unknown repo', "file_path": file_item.get('path')}, "tags": ["raw_code", file_item.get('path').split('.')[-1]]}


class PersistenceAgent(Agent):
    """(Unaltered) Archives multiple data types to the filesystem."""
    def __init__(self, name="PersistenceAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        self.output_dir = config.get("output_dir", "./final_training_data")
        if os.path.exists(self.output_dir): shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)
        if self.message_bus: self.message_bus.subscribe(ArchitectureEventType.TRAINING_TASK_CREATED, self)

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.TRAINING_TASK_CREATED:
            await self.save_task_jsonl(msg.get('task'))

    async def save_task_jsonl(self, task):
        target_dir = os.path.join(self.output_dir, task.get("type", "generic"))
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, "tasks.jsonl")
        print(f"PersistenceAgent: Archiving task '{task.get('task_id')}' to '{file_path}'")
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')


# ==============================================================================
# 3. DEMONSTRATION ORCHESTRATOR
# ==============================================================================

async def main():
    print("--- Orchestration Starting: Autonomous Discovery Pipeline ---")
    bus = CentralMessageBus()
    
    agents = [
        DiscoveryAgent(name="DiscoveryAgent", message_bus=bus),
        DataCreatorAgent(name="DataCreatorAgent", message_bus=bus),
        EnrichmentAgent(name="EnrichmentAgent", message_bus=bus),
        PersistenceAgent(name="PersistenceAgent", message_bus=bus)
    ]
    for agent in agents: bus.register_agent(agent.name, agent.inbox)
    
    agent_tasks = [asyncio.create_task(agent.run()) for agent in agents]

    print("\n--- Triggering the Autonomous Discovery ---\n")
    # This single command now triggers the entire dynamic pipeline
    agents[0].send({"type": ArchitectureEventType.DISCOVER_NEW_DATA})
    
    await asyncio.sleep(15) # Allow time for API calls, cloning, and processing

    print("\n\n--- Final Data Product ---")
    output_base_dir = agents[-1].output_dir
    for root, _, files in os.walk(output_base_dir):
        for f in files:
            path = os.path.join(root, f)
            print(f"\n📄 FILE: {os.path.relpath(path, output_base_dir)}")
            with open(path, 'r', encoding='utf-8') as fin:
                print(f"  - Wrote {len(fin.readlines())} training tasks.")
    
    # Shutdown
    for task in agent_tasks: task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    print("\n--- Orchestration Finished ---")

if __name__ == "__main__":
    asyncio.run(main())