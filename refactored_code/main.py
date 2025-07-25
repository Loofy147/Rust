import asyncio
import os
import logging
import time
import json
import re
import fnmatch
import subprocess
import shutil
import random
import yaml # PyYAML must be installed: pip install pyyaml

# --- Professional Improvement: Centralized Logging Setup ---
# In a real project, this would be in `src/utils/logging_setup.py`
def setup_logging(config):
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO').upper(), logging.INFO)
    fmt = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(level=level, format=fmt)
    
    # Optional: Log to a file
    if 'file' in log_config:
        file_handler = logging.FileHandler(log_config['file'])
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(fmt))
        logging.getLogger().addHandler(file_handler)
    
    logging.info("Logging framework initialized.")

# --- Professional Improvement: Enhanced Repo Extraction (Generator) ---
# In a real project, this would be in `src/utils/file_system.py`
def extract_repo_data_generator(repo_path, config):
    """
    Traverses a repository and YIELDS file content one by one to save memory.
    """
    proc_config = config.get('repo_processing', {})
    include_patterns = proc_config.get('include_patterns', ['*.py'])
    exclude_patterns = proc_config.get('exclude_patterns', [])
    
    logging.info(f"Starting data extraction from '{repo_path}' with {len(include_patterns)} include patterns.")
    
    if not os.path.isdir(repo_path):
        logging.error(f"Repository path '{repo_path}' is not a valid directory.")
        return

    repo_name = os.path.basename(os.path.normpath(repo_path))
    file_count = 0
    for root, _, files in os.walk(repo_path, topdown=True):
        # Efficiently prune excluded directories
        if any(fnmatch.fnmatch(os.path.join(root, d), pattern) for d in os.listdir(root) for pattern in exclude_patterns if pattern.endswith('/*')):
            continue

        for filename in files:
            file_path = os.path.join(root, filename)
            relative_file_path = os.path.relpath(file_path, repo_path)

            if any(fnmatch.fnmatch(relative_file_path, pattern) for pattern in exclude_patterns):
                continue

            if any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    file_count += 1
                    yield {
                        "repo_name": repo_name,
                        "file_path": relative_file_path,
                        "content": content
                    }
                except Exception as e:
                    logging.warning(f"Could not read file {file_path}: {e}")
    
    logging.info(f"Finished extraction from {repo_path}. Yielded {file_count} files.")


# --- Base classes remain largely the same but will use logging ---
# In a real project, these would be in `src/core/` and `src/agents/`
class Agent:
    def __init__(self, name="BaseAgent", message_bus=None, config=None):
        self.name = name
        self.inbox = []
        self.config = config.get(name, {}) if config else {} # Agent-specific config
        self.state = "idle"
        self.message_bus = message_bus
        self.logger = logging.getLogger(self.name) # Each agent gets its own logger
        self.logger.info(f"Agent initialized. State: {self.state}")

    def send(self, message, target_agent_name=None):
        if self.message_bus:
            if target_agent_name:
                self.logger.debug(f"Sending direct message to '{target_agent_name}'.")
                asyncio.create_task(self.message_bus.publish(message, target=target_agent_name))
            elif message.get('type'):
                self.logger.debug(f"Publishing event of type '{message.get('type')}'.")
                asyncio.create_task(self.message_bus.publish(message))
        else:
            self.logger.warning("Message bus not configured. Message not sent.")
            
    async def run(self):
        self.logger.info("Starting run loop.")
        self.state = "running"
        try:
            while True:
                if self.inbox:
                    msg = self.inbox.pop(0)
                    self.logger.debug(f"Handling message from inbox: {msg.get('type')}")
                    await self.handle_message(msg)
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            self.logger.info("Run loop cancelled.")
        except Exception as e:
            self.logger.error(f"FATAL error in run loop: {e}", exc_info=True)
        finally:
            self.state = "stopped"
            self.logger.info(f"Run loop finished. Final State: {self.state}")
            
    async def handle_message(self, msg):
        self.logger.warning(f"handle_message not implemented. Dropping message: {msg}")
        pass

class CentralMessageBus:
    # (This class is mostly fine, just add logging)
    def __init__(self):
        self._agent_inboxes = {}
        self._subscriptions = {}
        self.logger = logging.getLogger("CentralMessageBus")
        self.logger.info("Initialized.")

    def register_agent(self, agent_name, inbox_ref):
        if agent_name in self._agent_inboxes:
            self.logger.warning(f"Agent '{agent_name}' already registered. Overwriting.")
        self._agent_inboxes[agent_name] = inbox_ref
        self.logger.info(f"Agent '{agent_name}' inbox registered.")

    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]:
            self._subscriptions[event_type].append(agent)
            self.logger.info(f"Agent '{agent.name}' subscribed to '{event_type}'.")

    async def publish(self, message, target=None):
        if target:
            if target in self._agent_inboxes:
                self._agent_inboxes[target].append(message)
            else:
                self.logger.warning(f"Target agent '{target}' not found. Message dropped.")
        elif event_type := message.get('type'):
            if event_type in self._subscriptions:
                for agent in self._subscriptions[event_type]:
                    agent.inbox.append(message)
        else:
            self.logger.error("Publish failed: No target and no 'type' in message.")
            
class ArchitectureEventType:
    # (No changes needed here)
    REPO_DATA_EXTRACTED = "repo_data_extracted"
    CLONE_AND_EXTRACT_REPO_REQUEST = "clone_and_extract_repo_request"
    # ... other types

# --- Refactored DataCreatorAgent ---
class DataCreatorAgent(Agent):
    def __init__(self, name="DataCreatorAgent", message_bus=None, config=None):
        super().__init__(name=name, message_bus=message_bus, config=config)
        self.state = "waiting_for_task"
        self._processed_repo_tasks = set()
        # Using config for the clone directory
        self.clone_dir = self.config.get("clone_dir", "./cloned_repos")
        os.makedirs(self.clone_dir, exist_ok=True)
        if self.message_bus:
            # Task name is now more explicit
            self.message_bus.subscribe(ArchitectureEventType.CLONE_AND_EXTRACT_REPO_REQUEST, self)

    async def handle_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == ArchitectureEventType.CLONE_AND_EXTRACT_REPO_REQUEST:
            repo_url = msg.get("repo_url")
            if repo_url in self._processed_repo_tasks:
                self.logger.info(f"Skipping already processed repository '{repo_url}'.")
                return
            
            self.state = "processing_repo"
            self.logger.info(f"State change: {self.state}")
            await self.process_repo_clone_and_extract(msg)
            self._processed_repo_tasks.add(repo_url)
            self.state = "waiting_for_task"
            self.logger.info(f"State change: {self.state}")
        else:
            self.logger.warning(f"Ignoring unsupported message type '{msg_type}'.")

    async def process_repo_clone_and_extract(self, msg):
        repo_url = msg.get("repo_url")
        if not repo_url:
            self.logger.error("'clone_and_extract_repo' message missing 'repo_url'.")
            return

        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_repo_path = os.path.join(self.clone_dir, repo_name)
        
        self.logger.info(f"Starting clone for '{repo_url}' into '{local_repo_path}'")

        try:
            # --- CLONING ---
            def do_clone():
                if os.path.exists(local_repo_path):
                    shutil.rmtree(local_repo_path)
                subprocess.run(['git', 'clone', '--depth', '1', repo_url, local_repo_path], check=True)
            await asyncio.to_thread(do_clone)
            self.logger.info(f"Successfully cloned '{repo_url}'.")

            # --- EXTRACTION & BATCHING ---
            batch_size = self.config.get('repo_processing', {}).get('batch_size', 100)
            batch = []
            file_generator = extract_repo_data_generator(local_repo_path, self.config)
            
            for file_data in file_generator:
                batch.append(file_data)
                if len(batch) >= batch_size:
                    self.logger.info(f"Publishing a batch of {len(batch)} files from '{repo_name}'.")
                    self.send({
                        "type": ArchitectureEventType.REPO_DATA_EXTRACTED,
                        "source_repo": repo_url,
                        "data": batch
                    })
                    batch = [] # Reset batch
            
            # Send any remaining files in the last batch
            if batch:
                self.logger.info(f"Publishing the final batch of {len(batch)} files from '{repo_name}'.")
                self.send({
                    "type": ArchitectureEventType.REPO_DATA_EXTRACTED,
                    "source_repo": repo_url,
                    "data": batch
                })

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to clone repo '{repo_url}'. Git error: {e}", exc_info=True)
            self.send({"type": "error", "details": f"Failed to clone {repo_url}", "original_message": msg}, "Orchestrator")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while processing repo '{repo_url}': {e}", exc_info=True)
            self.send({"type": "error", "details": str(e), "original_message": msg}, "Orchestrator")
        finally:
            if os.path.exists(local_repo_path):
                self.logger.info(f"Cleaning up by removing '{local_repo_path}'.")
                shutil.rmtree(local_repo_path)


# --- Example Orchestration with Professional Setup ---
async def main():
    # 1. Load configuration
    try:
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logging.basicConfig(level=logging.ERROR)
        logging.error("FATAL: config.yaml not found. Please create it.")
        return
        
    # 2. Setup logging based on config
    setup_logging(config)
    
    # 3. Initialize components with config
    bus = CentralMessageBus()
    orchestrator = Agent(name="Orchestrator", message_bus=bus, config=config)
    data_creator = DataCreatorAgent(name="DataCreatorAgent", message_bus=bus, config=config)
    
    # 4. Agent to consume the extracted data
    class IngestionAgent(Agent):
        def __init__(self, name="IngestionAgent", message_bus=None, config=None):
            super().__init__(name, message_bus, config)
            if self.message_bus:
                self.message_bus.subscribe(ArchitectureEventType.REPO_DATA_EXTRACTED, self)
        
        async def handle_message(self, msg):
            if msg.get("type") == ArchitectureEventType.REPO_DATA_EXTRACTED:
                repo = msg.get('source_repo')
                data_count = len(msg.get('data', []))
                self.logger.info(f"<<<<< RECEIVED BATCH of {data_count} files from {repo} >>>>>")

    ingestion_agent = IngestionAgent(name="IngestionAgent", message_bus=bus, config=config)

    # 5. Register agents
    bus.register_agent(orchestrator.name, orchestrator.inbox)
    bus.register_agent(data_creator.name, data_creator.inbox)
    bus.register_agent(ingestion_agent.name, ingestion_agent.inbox)

    # 6. Start agent tasks
    agent_tasks = [
        asyncio.create_task(data_creator.run()),
        asyncio.create_task(ingestion_agent.run())
    ]
    
    logging.info("--- Agents are running. Sending initial tasks. ---")
    
    # 7. Orchestrator sends a task
    repo_to_clone = "https://github.com/huggingface/knockknock"
    orchestrator.send({
        "type": ArchitectureEventType.CLONE_AND_EXTRACT_REPO_REQUEST,
        "repo_url": repo_to_clone
    })
    
    # 8. Run and shutdown
    await asyncio.sleep(15)
    logging.info("--- Shutting down agents ---")
    for task in agent_tasks:
        task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    logging.info("--- Orchestration Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
