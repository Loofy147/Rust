import asyncio
import os
import logging
import time
import json
import re
import fnmatch # Import fnmatch
import textwrap # Import textwrap
import markdown # Import markdown
from bs4 import BeautifulSoup # Import BeautifulSoup
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
        print(f"Placeholder Agent '{self.name}' initialized. State: {self.state}")

    def send(self, message, target_agent_name=None):
        """Sends a message via the message bus, either directly or as an event."""
        if self.message_bus:
            if target_agent_name:
                 print(f"Agent '{self.name}' sending direct message to '{target_agent_name}' via Message Bus.")
                 # Use asyncio.create_task to send without blocking the agent's main loop
                 asyncio.create_task(self.message_bus.publish(message, target=target_agent_name))
            elif message.get('type'):
                 print(f"Agent '{self.name}' publishing event of type '{message.get('type')}' via Message Bus.")
                 asyncio.create_task(self.message_bus.publish(message))
            else:
                 print(f"Agent '{self.name}' Warning: Cannot send message. No target agent specified and message is missing 'type' field.")
        else:
            print(f"Agent '{self.name}' Warning: Message bus not configured. Message not sent.")

    async def run(self):
        print(f"Agent '{self.name}' starting run loop. Current State: {self.state}")
        self.state = "running"
        try:
            while True:
                if self.inbox:
                     msg = self.inbox.pop(0)
                     print(f"Agent '{self.name}' picking up message from internal inbox. Current State: {self.state}")
                     await self.handle_message(msg)

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            print(f"Agent '{self.name}' run loop cancelled. State: stopping")
        except Exception as e:
            print(f"Agent '{self.name}' encountered error: {e}. State: error")
        finally:
             self.state = "stopped"
             print(f"Agent '{self.name}' run loop finished. Final State: {self.state}")

    async def handle_message(self, msg):
        print(f"Agent '{self.name}' handling message: {msg}. Current State: {self.state}")
        print(f"Agent '{self.name}' processed unsupported message type or is in an incompatible state.")
        pass


# Ensure CentralMessageBus is defined
class CentralMessageBus:
    def __init__(self):
        self._agent_inboxes = {}
        self._subscriptions = {}
        print("CentralMessageBus initialized.")

    def register_agent(self, agent_name, inbox_ref):
        if agent_name in self._agent_inboxes:
            print(f"Warning: Agent '{agent_name}' inbox already registered. Overwriting registration.")
        self._agent_inboxes[agent_name] = inbox_ref
        print(f"Message Bus: Agent '{agent_name}' inbox registered.")

    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]:
            self._subscriptions[event_type].append(agent)
            print(f"Message Bus: Agent '{agent.name}' subscribed to event type: {event_type}")
        else:
             print(f"Message Bus Warning: Agent '{agent.name}' is already subscribed to event type: {event_type}.")

    def unsubscribe(self, event_type, agent):
        if event_type in self._subscriptions and agent in self._subscriptions[event_type]:
            self._subscriptions[event_type].remove(agent)
            print(f"Message Bus: Agent '{agent.name}' unsubscribed from event type: {event_type}")

    async def publish(self, message, target=None):
        event_type = message.get('type')
        if target:
            if target in self._agent_inboxes:
                target_inbox = self._agent_inboxes[target]
                target_inbox.append(message)
            else:
                print(f"Message Bus Publish Warning: Target agent '{target}' not found in _agent_inboxes. Direct message not delivered.")
        elif event_type:
            if event_type in self._subscriptions:
                for agent in list(self._subscriptions[event_type]):
                     if hasattr(agent, 'inbox'):
                         agent.inbox.append(message)
                     else:
                         print(f"Message Bus Publish (Event) Warning: Agent {agent.name} has no inbox to deliver message.")
            else:
                 pass # No subscribers is not an error, just means no one is listening
        else:
             print(f"Message Bus Publish Warning: Cannot publish message. No target agent specified and message is missing 'type' field.")


# Ensure ArchitectureEventType is defined with all necessary types
class ArchitectureEventType:
    CODE_CHANGE = "code_change"
    ARCHITECTURE_UPDATE = "architecture_update"
    DEPLOYMENT = "deployment"
    SECURITY_ALERT = "security_alert"
    TEST_RESULT = "test_result"
    PERFORMANCE_ALERT = "performance_alert"
    MICROSERVICE_EVENT = "microservice_event"
    USER_FEEDBACK = "user_feedback"
    STRUCTURED_DATA = "structured_data"
    RAW_TEXT_DATA = "raw_text_data"
    CODE_SNIPPET_DATA = "code_snippet_data"
    USER_FEEDBACK_PROCESSED = "user_feedback_processed"
    REPO_DATA_EXTRACTED = "repo_data_extracted" # New event type
    INGEST_REPOSITORY = "ingest_repository" # New message type for Orchestrator
    PROCESSED_TEXT = "processed_text" # From ProcessingAgent example
    INGESTED_FILE_CONTENT = "ingested_file_content" # From IngestionAgent
    INGESTED_TEXT = "ingested_text" # From IngestionAgent
    INGESTED_DATA_BATCH = "ingested_data_batch" # From IngestionAgent
    GENERATED_CODE = "generated_code" # From CodeGeneratorAgent
    CODE_FOR_ANALYSIS = "code_for_analysis" # From CodeGeneratorAgent
    ANALYZED_CODE_STRUCTURE = "analyzed_code_structure" # New type for code analysis results
    ANALYZED_DOCUMENTATION = "analyzed_documentation" # New type for doc analysis results
    AGENT_ANALYSIS_REPORT = "agent_analysis_report" # New type for findings
    IMPROVEMENT_SUGGESTION = "improvement_suggestion" # New type for suggestions


# Ensure extract_repo_data function is defined
def extract_repo_data(repo_path, include_patterns=['*.py', '*.md', '*.ipynb'], exclude_patterns=['.git/*', '.DS_Store']):
    """
    Traverses a repository directory, extracts content from files matching include patterns,
    and excludes files matching exclude patterns.
    """
    extracted_data = []
    print(f"\nExtracting data from repository: {repo_path}")

    if not os.path.isdir(repo_path):
        print(f"Error: Repository path '{repo_path}' is not a valid directory.")
        return extracted_data

    repo_name = os.path.basename(os.path.normpath(repo_path))
    for root, _, files in os.walk(repo_path):
        # Prune the .git directory directly in os.walk to be more efficient
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

                    extracted_data.append({
                        "repo_name": repo_name,
                        "file_path": relative_file_path,
                        "content": content
                    })
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    print(f"Finished extraction from {repo_path}. Extracted {len(extracted_data)} files.")
    return extracted_data


# Define the DataCreatorAgent class
class DataCreatorAgent(Agent):
    def __init__(self, name="DataCreatorAgent", message_bus=None, config=None):
        super().__init__(name=name, message_bus=message_bus, config=config)
        print(f"DataCreatorAgent '{self.name}' initialized.")
        self.state = "waiting_for_task"
        self._processed_feedback_ids = set()
        self._feedback_parsing_patterns = {
            "bug_report": re.compile(r"(?:bug report|issue):?\s*(.*)", re.IGNORECASE | re.DOTALL),
            "feature_request": re.compile(r"(?:feature request|suggest|idea):?\s*(.*)", re.IGNORECASE | re.DOTALL),
            "code_generation_request": re.compile(r"(?:generate code|write a function):?\s*(.*)", re.IGNORECASE | re.DOTALL),
        }
        self._processed_repo_tasks = set()
        self.clone_dir = self.config.get("clone_dir", "./cloned_repos")
        os.makedirs(self.clone_dir, exist_ok=True)


        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.USER_FEEDBACK, self)
            # This agent now listens for the specific task to clone a repo
            self.message_bus.subscribe("clone_and_extract_repo", self)
            print(f"DataCreatorAgent '{self.name}' subscribed to task events.")


    async def handle_message(self, msg):
        """Handle incoming messages."""
        print(f"DataCreatorAgent '{self.name}' handling message: {msg}. Current State: {self.state}")

        msg_type = msg.get("type")
        msg_id = msg.get("id", f"{msg_type}-{int(time.time())}-{random.randint(1000,9999)}")

        # Create a unique ID for repo tasks to prevent re-cloning
        if msg_type == "clone_and_extract_repo":
            repo_url = msg.get("repo_url")
            if repo_url in self._processed_repo_tasks:
                print(f"DataCreatorAgent: Skipping already processed repository '{repo_url}'.")
                return
            self._processed_repo_tasks.add(repo_url)

        if msg_type == ArchitectureEventType.USER_FEEDBACK:
            if msg_id in self._processed_feedback_ids:
                print(f"DataCreatorAgent: Skipping already processed feedback with ID {msg_id}.")
                return
            self._processed_feedback_ids.add(msg_id)

        # Main task handling logic
        supported_types = [ArchitectureEventType.USER_FEEDBACK, "clone_and_extract_repo"]
        if self.state == "waiting_for_task" and msg_type in supported_types:
            self.state = "processing_task"
            try:
                if msg_type == ArchitectureEventType.USER_FEEDBACK:
                    await self.process_user_feedback(msg)
                elif msg_type == "clone_and_extract_repo":
                    await self.process_repo_clone_and_extract(msg)
            except Exception as e:
                 logging.error(f"DataCreatorAgent Error processing message ID {msg_id}: {e}", exc_info=True)
                 self.send({"type": "error", "details": f"Error processing message ID {msg_id}: {e}", "original_message": msg}, "Orchestrator")
            finally:
                self.state = "waiting_for_task"
        else:
            print(f"DataCreatorAgent '{self.name}': Ignoring message type '{msg_type}' in state '{self.state}'.")


    async def process_user_feedback(self, feedback_msg):
        """Processes user feedback, parses it, and emits a structured event."""
        print(f"DataCreatorAgent: Processing user feedback: {feedback_msg}")
        feedback_text = feedback_msg.get("feedback", "")
        if not feedback_text:
            return

        parsed = False
        for category, pattern in self._feedback_parsing_patterns.items():
            match = pattern.match(feedback_text)
            if match:
                extracted_content = match.group(1).strip()
                processed_message = {
                    "type": ArchitectureEventType.USER_FEEDBACK_PROCESSED,
                    "category": category,
                    "content": extracted_content,
                    "source_message_id": feedback_msg.get("id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                print(f"DataCreatorAgent: Parsed feedback as '{category}'. Publishing structured event.")
                self.send(processed_message) # Broadcast the structured feedback
                parsed = True
                break
        
        if not parsed:
            print("DataCreatorAgent: Feedback did not match any known patterns. Forwarding as generic text.")
            # Optionally, forward as a raw text event for other agents
            self.send({
                "type": ArchitectureEventType.RAW_TEXT_DATA,
                "content": feedback_text,
                "source": "user_feedback"
            })

    async def process_repo_clone_and_extract(self, msg):
        """Clones a Git repository, extracts file contents, and publishes the data."""
        repo_url = msg.get("repo_url")
        if not repo_url:
            print("DataCreatorAgent Error: 'clone_and_extract_repo' message missing 'repo_url'.")
            self.send({"type": "error", "details": "Missing 'repo_url'", "original_message": msg}, "Orchestrator")
            return

        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_repo_path = os.path.join(self.clone_dir, repo_name)
        
        print(f"DataCreatorAgent: Starting clone for '{repo_url}' into '{local_repo_path}'")

        try:
            # --- CLONING ---
            # Run the blocking git clone command in a separate thread
            def do_clone():
                if os.path.exists(local_repo_path):
                     shutil.rmtree(local_repo_path)
                process = subprocess.run(
                    ['git', 'clone', repo_url, local_repo_path],
                    capture_output=True, text=True, check=True
                )
                return process.returncode == 0
            
            clone_success = await asyncio.to_thread(do_clone)

            if not clone_success:
                raise Exception("Git clone command failed.")

            print(f"DataCreatorAgent: Successfully cloned '{repo_url}'.")

            # --- EXTRACTION ---
            # Use the existing extraction utility function
            extracted_data = extract_repo_data(local_repo_path)

            if not extracted_data:
                print(f"DataCreatorAgent Warning: No data extracted from '{repo_url}'. Might be empty or have no matching files.")
                self.send({"type": "warning", "details": "No data extracted from repo", "source_repo": repo_url}, "Orchestrator")
                return

            # --- PUBLISHING ---
            # This is the real data you wanted. Publish it for other agents.
            data_message = {
                "type": ArchitectureEventType.REPO_DATA_EXTRACTED,
                "source_repo": repo_url,
                "data": extracted_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            print(f"DataCreatorAgent: Publishing {len(extracted_data)} files from '{repo_url}' to the message bus.")
            self.send(data_message) # Broadcast to any interested agent

        except subprocess.CalledProcessError as e:
            error_message = f"Failed to clone repo '{repo_url}'. Git error: {e.stderr}"
            print(f"DataCreatorAgent Error: {error_message}")
            self.send({"type": "error", "details": error_message, "original_message": msg}, "Orchestrator")
        except Exception as e:
            error_message = f"An unexpected error occurred while processing repo '{repo_url}': {e}"
            logging.error(error_message, exc_info=True)
            self.send({"type": "error", "details": error_message, "original_message": msg}, "Orchestrator")
        finally:
            # --- CLEANUP ---
            # Always try to remove the cloned repository to save space
            if os.path.exists(local_repo_path):
                print(f"DataCreatorAgent: Cleaning up by removing '{local_repo_path}'.")
                try:
                    shutil.rmtree(local_repo_path)
                except OSError as e:
                    print(f"DataCreatorAgent Cleanup Error: Failed to remove directory {local_repo_path}: {e}")

# ==============================================================================
# Example Execution - This demonstrates how to use the system
# ==============================================================================
async def main():
    print("--- Orchestration Starting ---")
    
    # 1. Initialize core components
    bus = CentralMessageBus()
    
    # 2. Initialize Agents
    # The Orchestrator would likely be a more complex agent, but we use a placeholder for this example.
    orchestrator = Agent(name="Orchestrator", message_bus=bus)
    data_creator = DataCreatorAgent(name="DataCreatorAgent", message_bus=bus)

    # 3. Register Agents with the Message Bus
    # The bus needs to know where to send direct messages
    bus.register_agent(orchestrator.name, orchestrator.inbox)
    bus.register_agent(data_creator.name, data_creator.inbox)
    
    # Let's create a listener agent to see the result of the data extraction
    class IngestionAgent(Agent):
        def __init__(self, name="IngestionAgent", message_bus=None, config=None):
            super().__init__(name, message_bus, config)
            if self.message_bus:
                self.message_bus.subscribe(ArchitectureEventType.REPO_DATA_EXTRACTED, self)

        async def handle_message(self, msg):
            if msg.get("type") == ArchitectureEventType.REPO_DATA_EXTRACTED:
                print("\n\n<<<<< IngestionAgent RECEIVED REAL DATA! >>>>>")
                repo = msg.get('source_repo')
                data_count = len(msg.get('data', []))
                print(f"Source Repository: {repo}")
                print(f"Number of files processed: {data_count}")
                # In a real scenario, this agent would now process this data:
                # - Save to a vector database
                # - Create embeddings
                # - Prepare training batches for Mistral
                first_file = msg['data'][0] if data_count > 0 else {}
                print(f"Sample File Path: {first_file.get('file_path')}")
                print(f"Sample Content (first 100 chars): '{first_file.get('content', '')[:100].replace(os.linesep, ' ')}...'")
                print("<<<<< IngestionAgent finished processing batch. >>>>>\n\n")

    ingestion_agent = IngestionAgent(name="IngestionAgent", message_bus=bus)
    bus.register_agent(ingestion_agent.name, ingestion_agent.inbox)

    # 4. Start agent background tasks
    agent_tasks = [
        asyncio.create_task(data_creator.run()),
        asyncio.create_task(ingestion_agent.run())
    ]
    
    print("\n--- Agents are running. Sending initial tasks. ---\n")
    
    # 5. Orchestrator sends a task to the DataCreatorAgent
    # This is the key message to trigger real data extraction.
    # We will use a small, public repository for this example.
    repo_to_clone = "https://github.com/huggingface/knockknock"
    
    orchestrator.send({
        "type": "clone_and_extract_repo",
        "repo_url": repo_to_clone
    })
    
    # Let's also send a user feedback message to test that pathway
    orchestrator.send({
        "type": ArchitectureEventType.USER_FEEDBACK,
        "feedback": "Idea: could you add a feature to automatically summarize the extracted code?"
    })

    # 6. Run the simulation for a short period
    await asyncio.sleep(15) # Allow time for cloning, extraction, and processing

    # 7. Cleanly shut down agents
    print("\n--- Shutting down agents ---")
    for task in agent_tasks:
        task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    
    print("--- Orchestration Finished ---")

if __name__ == "__main__":
    # Ensure you have git installed and accessible in your system's PATH
    # To run this, save the code and execute `python your_script_name.py`
    asyncio.run(main())