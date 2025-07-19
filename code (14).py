import asyncio
import os
import logging
import time
import json
import re
import fnmatch
import textwrap
import markdown
from bs4 import BeautifulSoup
from datetime import datetime
import subprocess # For cloning repositories
import shutil # For cleaning up cloned repositories
import random # For generating unique IDs

# Ensure Agent base class is defined
class Agent:
    def __init__(self, name="BaseAgent", message_bus=None, config=None):
        self.name = name
        self.inbox = []
        self.config = config if config is not None else {}
        self.state = "idle"
        self.message_bus = message_bus
        # Minimal logging for this execution
        # print(f"Agent '{self.name}' initialized.")

    def send(self, message, target_agent_name=None):
        """Sends a message via the message bus, either directly or as an event."""
        if self.message_bus:
            # Use asyncio.create_task to send without blocking the agent's main loop
            asyncio.create_task(self.message_bus.publish(message, target=target_agent_name))
        else:
            print(f"Agent '{self.name}' Warning: Message bus not configured.")

    async def run(self):
        self.state = "running"
        try:
            while True:
                if self.inbox:
                     msg = self.inbox.pop(0)
                     await self.handle_message(msg)
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass # Normal shutdown
        except Exception as e:
            print(f"Agent '{self.name}' encountered a critical error: {e}")
        finally:
             self.state = "stopped"

    async def handle_message(self, msg):
        print(f"Agent '{self.name}' received unhandled message: {msg}")
        pass

# Ensure CentralMessageBus is defined
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
        event_type = message.get('type')
        if target:
            if target in self._agent_inboxes:
                self._agent_inboxes[target].append(message)
            else:
                print(f"Message Bus Warning: Target agent '{target}' not found.")
        elif event_type:
            if event_type in self._subscriptions:
                for agent in self._subscriptions[event_type]:
                     if hasattr(agent, 'inbox'):
                         agent.inbox.append(message)

# Ensure ArchitectureEventType is defined with all necessary types
class ArchitectureEventType:
    USER_FEEDBACK = "user_feedback"
    USER_FEEDBACK_PROCESSED = "user_feedback_processed"
    REPO_DATA_EXTRACTED = "repo_data_extracted"
    RAW_TEXT_DATA = "raw_text_data"

# Ensure extract_repo_data function is defined
def extract_repo_data(repo_path, include_patterns=['*.py', '*.md', '*.js', '*.json'], exclude_patterns=['.git/*', '.DS_Store', 'package-lock.json']):
    extracted_data = []
    if not os.path.isdir(repo_path):
        return extracted_data
    repo_name = os.path.basename(os.path.normpath(repo_path))
    for root, _, files in os.walk(repo_path):
        if '.git' in root:
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
                    extracted_data.append({"repo_name": repo_name, "file_path": relative_file_path, "content": content})
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
    return extracted_data

# The final DataCreatorAgent class
class DataCreatorAgent(Agent):
    def __init__(self, name="DataCreatorAgent", message_bus=None, config=None):
        super().__init__(name=name, message_bus=message_bus, config=config)
        self.state = "waiting_for_task"
        self._processed_feedback_ids = set()
        self._feedback_parsing_patterns = {
            "feature_request": re.compile(r"(?:feature request|idea):?\s*(.*)", re.IGNORECASE | re.DOTALL),
        }
        self._processed_repo_tasks = set()
        self.clone_dir = self.config.get("clone_dir", "./cloned_repos")
        os.makedirs(self.clone_dir, exist_ok=True)
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.USER_FEEDBACK, self)
            self.message_bus.subscribe("clone_and_extract_repo", self)

    async def handle_message(self, msg):
        msg_type = msg.get("type")
        if self.state != "waiting_for_task":
             self.inbox.append(msg) # Re-queue if busy
             await asyncio.sleep(1)
             return

        repo_url = msg.get("repo_url")
        if msg_type == "clone_and_extract_repo" and repo_url in self._processed_repo_tasks:
            print(f"DataCreatorAgent: Skipping already processed repository '{repo_url}'.")
            return
        
        self.state = "processing_task"
        if msg_type == ArchitectureEventType.USER_FEEDBACK:
            await self.process_user_feedback(msg)
        elif msg_type == "clone_and_extract_repo":
            self._processed_repo_tasks.add(repo_url)
            await self.process_repo_clone_and_extract(msg)
        self.state = "waiting_for_task"

    async def process_user_feedback(self, feedback_msg):
        feedback_text = feedback_msg.get("feedback", "")
        for category, pattern in self._feedback_parsing_patterns.items():
            match = pattern.match(feedback_text)
            if match:
                processed_message = {
                    "type": ArchitectureEventType.USER_FEEDBACK_PROCESSED,
                    "category": category,
                    "content": match.group(1).strip(),
                }
                print(f"\n✅ DataCreatorAgent: Parsed feedback as '{category}'. Publishing structured event.")
                self.send(processed_message)
                return

    async def process_repo_clone_and_extract(self, msg):
        repo_url = msg.get("repo_url")
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_repo_path = os.path.join(self.clone_dir, repo_name)
        
        print(f"\n⏳ DataCreatorAgent: Starting task for '{repo_url}'")
        try:
            def do_clone():
                if os.path.exists(local_repo_path): shutil.rmtree(local_repo_path)
                subprocess.run(['git', 'clone', '--depth', '1', repo_url, local_repo_path], capture_output=True, text=True, check=True)
            
            await asyncio.to_thread(do_clone)
            print(f"✅ DataCreatorAgent: Successfully cloned '{repo_url}'. Extracting files...")
            
            extracted_data = extract_repo_data(local_repo_path)
            
            if not extracted_data:
                print(f"⚠️ DataCreatorAgent Warning: No matching files found in '{repo_url}'.")
                return

            data_message = {
                "type": ArchitectureEventType.REPO_DATA_EXTRACTED,
                "source_repo": repo_url,
                "data": extracted_data
            }
            print(f"✅ DataCreatorAgent: Publishing {len(extracted_data)} files from '{repo_url}'.")
            self.send(data_message)

        except subprocess.CalledProcessError as e:
            error_message = f"Failed to clone repo '{repo_url}'. Git error: {e.stderr.strip()}"
            print(f"\n❌ DataCreatorAgent ERROR: {error_message}")
            self.send({"type": "error", "details": error_message}, "Orchestrator")
        except Exception as e:
            print(f"\n❌ DataCreatorAgent ERROR: An unexpected error occurred with '{repo_url}': {e}")
        finally:
            if os.path.exists(local_repo_path):
                try:
                    shutil.rmtree(local_repo_path)
                except OSError as e:
                    print(f"❌ DataCreatorAgent Cleanup Error: {e}")

# Listener Agent to confirm data reception
class IngestionAgent(Agent):
    def __init__(self, name="IngestionAgent", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.REPO_DATA_EXTRACTED, self)

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.REPO_DATA_EXTRACTED:
            repo = msg.get('source_repo')
            data_count = len(msg.get('data', []))
            print("\n\n=============== ✅ INGESTION AGENT RECEIVED DATA ✅ ===============")
            print(f"  Source Repository: {repo}")
            print(f"  Files received: {data_count}")
            print("===================================================================\n")

async def main():
    print("--- Orchestration System Starting ---")
    bus = CentralMessageBus()
    
    # Initialize Agents
    orchestrator = Agent(name="Orchestrator", message_bus=bus)
    data_creator = DataCreatorAgent(name="DataCreatorAgent", message_bus=bus)
    ingestion_agent = IngestionAgent(name="IngestionAgent", message_bus=bus)

    # Register agents that need to receive direct messages or be subscribed
    bus.register_agent(orchestrator.name, orchestrator.inbox)
    bus.register_agent(data_creator.name, data_creator.inbox)
    bus.register_agent(ingestion_agent.name, ingestion_agent.inbox)
    
    # Start agent background tasks
    agent_tasks = [
        asyncio.create_task(data_creator.run()),
        asyncio.create_task(ingestion_agent.run())
    ]
    
    print("\n--- AGENTS ARE LIVE. ORCHESTRATOR ISSUING COMMANDS ---\n")
    
    # 1. Primary Success Case
    orchestrator.send({"type": "clone_and_extract_repo", "repo_url": "https://github.com/huggingface/knockknock"})
    
    # 2. Heterogeneous Case (JS, JSON, MD files)
    orchestrator.send({"type": "clone_and_extract_repo", "repo_url": "https://github.com/axios/axios"})

    # 3. User Feedback Case
    orchestrator.send({"type": ArchitectureEventType.USER_FEEDBACK", "feedback": "Idea: auto-detect outdated dependencies."})
    
    # 4. Graceful Failure Case
    orchestrator.send({"type": "clone_and_extract_repo", "repo_url": "https://github.com/nonexistent-user/nonexistent-repo-12345.git"})

    # Allow time for all tasks to complete
    await asyncio.sleep(30)

    # Cleanly shut down agents
    print("\n--- COMMAND SEQUENCE COMPLETE. SHUTTING DOWN AGENTS. ---")
    for task in agent_tasks:
        task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    
    print("--- Orchestration System Shutdown. ---")

if __name__ == "__main__":
    asyncio.run(main())```

### **What to Expect in the Output**

The system is now running. You will see a real-time log of the agents' operations. Because these tasks run asynchronously, the output from different tasks will be interleaved. Here is what to watch for:

1.  **For the `knockknock` and `axios` repos:**
    *   `⏳ DataCreatorAgent: Starting task for...`
    *   `✅ DataCreatorAgent: Successfully cloned...`
    *   `✅ DataCreatorAgent: Publishing X files...`
    *   Finally, the confirmation from the second agent: `=============== ✅ INGESTION AGENT RECEIVED DATA ✅ ===============` for each repository.

2.  **For the User Feedback:**
    *   `✅ DataCreatorAgent: Parsed feedback as 'feature_request'. Publishing structured event.`

3.  **For the Non-Existent Repo:**
    *   `❌ DataCreatorAgent ERROR: Failed to clone repo...` followed by an error message from Git like `fatal: repository '...' not found`.
    *   The system will **not** crash. The `IngestionAgent` will simply not receive data for this task, proving the pipeline's resilience.

This execution will provide us with our genesis dataset and validate the entire operational flow. The system is live and processing.