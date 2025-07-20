import asyncio
import os
import logging
import time
import json
import re
import fnmatch
import textwrap
import ast # CRITICAL IMPORT for intelligent Python chunking
from datetime import datetime
import subprocess
import shutil
import random

# --- BASE CLASSES (UNCHANGED) ---
class Agent:
    def __init__(self, name="BaseAgent", message_bus=None, config=None):
        self.name = name
        self.inbox = []
        self.config = config if config is not None else {}
        self.state = "idle"
        self.message_bus = message_bus
    def send(self, message, target_agent_name=None):
        if self.message_bus: asyncio.create_task(self.message_bus.publish(message, target=target_agent_name))
    async def run(self):
        self.state = "running"
        try:
            while True:
                if self.inbox: await self.handle_message(self.inbox.pop(0))
                else: await asyncio.sleep(0.1)
        except asyncio.CancelledError: pass
        finally: self.state = "stopped"
    async def handle_message(self, msg): print(f"Agent '{self.name}' received unhandled message: {msg}")

class CentralMessageBus:
    def __init__(self): self._agent_inboxes, self._subscriptions = {}, {}
    def register_agent(self, agent_name, inbox_ref): self._agent_inboxes[agent_name] = inbox_ref
    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions: self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]: self._subscriptions[event_type].append(agent)
    async def publish(self, message, target=None):
        event_type = message.get('type')
        if target and target in self._agent_inboxes: self._agent_inboxes[target].append(message)
        elif event_type and event_type in self._subscriptions:
            for agent in self._subscriptions[event_type]:
                if hasattr(agent, 'inbox'): agent.inbox.append(message)

# --- EVENT TYPES & UTILITIES (UPDATED) ---
class ArchitectureEventType:
    USER_FEEDBACK = "user_feedback"
    USER_FEEDBACK_PROCESSED = "user_feedback_processed"
    REPO_DATA_EXTRACTED = "repo_data_extracted"
    PROCESSED_DATA_CHUNKS = "processed_data_chunks" # New event for our new agent
    
def extract_repo_data(repo_path, include_patterns=['*.py', '*.md'], exclude_patterns=['.git/*']):
    extracted_data = []
    if not os.path.isdir(repo_path): return extracted_data
    repo_name = os.path.basename(os.path.normpath(repo_path))
    for root, _, files in os.walk(repo_path):
        if '.git' in root: continue
        for filename in files:
            file_path, relative_file_path = os.path.join(root, filename), os.path.relpath(file_path, repo_path)
            if any(fnmatch.fnmatch(relative_file_path, p) for p in exclude_patterns): continue
            if any(fnmatch.fnmatch(filename, p) for p in include_patterns):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    extracted_data.append({"repo_name": repo_name, "file_path": relative_file_path, "content": content})
                except Exception: pass
    return extracted_data

# --- AGENT DEFINITIONS (DataCreatorAgent is now more streamlined) ---

class DataCreatorAgent(Agent):
    def __init__(self, name="DataCreatorAgent", message_bus=None, config=None):
        super().__init__(name=name, message_bus=message_bus, config=config)
        self.state = "idle"
        self.clone_dir = self.config.get("clone_dir", "./cloned_repos")
        os.makedirs(self.clone_dir, exist_ok=True)
        if self.message_bus: self.message_bus.subscribe("clone_and_extract_repo", self)

    async def handle_message(self, msg):
        repo_url = msg.get("repo_url")
        if not repo_url or self.state == "processing": return
        
        self.state = "processing"
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_repo_path = os.path.join(self.clone_dir, repo_name)
        
        print(f"\n⏳ DataCreatorAgent: Starting clone for '{repo_url}'")
        try:
            def do_clone():
                if os.path.exists(local_repo_path): shutil.rmtree(local_repo_path)
                subprocess.run(['git', 'clone', '--depth', '1', repo_url, local_repo_path], capture_output=True, text=True, check=True)
            await asyncio.to_thread(do_clone)
            
            extracted_data = extract_repo_data(local_repo_path)
            if extracted_data:
                print(f"✅ DataCreatorAgent: Publishing {len(extracted_data)} files from '{repo_url}'.")
                self.send({"type": ArchitectureEventType.REPO_DATA_EXTRACTED, "source_repo": repo_url, "data": extracted_data})
        except Exception as e: print(f"❌ DataCreatorAgent ERROR cloning '{repo_url}': {e}")
        finally:
            if os.path.exists(local_repo_path): shutil.rmtree(local_repo_path)
            self.state = "idle"

# --- NEW AGENT: THE PROCESSING AGENT ---

class ProcessingAgent(Agent):
    """
    Subscribes to raw data events and processes them into structured, chunked data.
    """
    def __init__(self, name="ProcessingAgent", message_bus=None, config=None):
        super().__init__(name=name, message_bus=message_bus, config=config)
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.REPO_DATA_EXTRACTED, self)
            print("✅ ProcessingAgent is online and waiting for repository data.")

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.REPO_DATA_EXTRACTED:
            print(f"\n⏳ ProcessingAgent: Received {len(msg.get('data',[]))} files from '{msg.get('source_repo')}'. Starting chunking...")
            
            all_chunks = []
            for file_data in msg.get('data', []):
                file_path = file_data.get('file_path')
                content = file_data.get('content')
                
                if file_path.endswith('.py'):
                    chunks = self._chunk_python_code(content, file_path, msg.get('source_repo'))
                    all_chunks.extend(chunks)
                elif file_path.endswith('.md'):
                    chunks = self._chunk_markdown(content, file_path, msg.get('source_repo'))
                    all_chunks.extend(chunks)
            
            if all_chunks:
                print(f"✅ ProcessingAgent: Generated {len(all_chunks)} chunks. Publishing to message bus.")
                self.send({
                    "type": ArchitectureEventType.PROCESSED_DATA_CHUNKS,
                    "source_repo": msg.get('source_repo'),
                    "chunks": all_chunks
                })

    def _chunk_python_code(self, content, file_path, repo_name):
        """Chunks Python code using Abstract Syntax Tree parsing."""
        chunks = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    chunk_content = ast.get_source_segment(content, node)
                    if chunk_content:
                        chunks.append({
                            "repo_name": repo_name,
                            "file_path": file_path,
                            "chunk_type": "function" if isinstance(node, ast.FunctionDef) else "class",
                            "identifier": node.name,
                            "content": chunk_content
                        })
        except Exception as e:
            # If AST parsing fails, fall back to simple text chunking for the whole file
            print(f"⚠️  ProcessingAgent: AST parsing failed for {file_path} ({e}). Falling back to text chunking.")
            return self._chunk_text(content, file_path, repo_name, chunk_size=1000, chunk_overlap=100)
        return chunks

    def _chunk_markdown(self, content, file_path, repo_name):
        """Chunks Markdown by splitting at headers, then by paragraphs."""
        # Simple example: split by headers, then paragraphs
        chunks = []
        # Split by level 1 and 2 headers
        md_sections = re.split(r'(^##? .*)', content, flags=re.MULTILINE)
        for i in range(1, len(md_sections), 2):
            header = md_sections[i]
            section_content = md_sections[i+1]
            for paragraph in section_content.split('\n\n'):
                if paragraph.strip():
                    chunks.append({
                        "repo_name": repo_name,
                        "file_path": file_path,
                        "chunk_type": "markdown",
                        "identifier": header.strip(),
                        "content": f"{header}\n{paragraph.strip()}"
                    })
        return chunks

# --- LISTENER AGENT TO VERIFY THE PIPELINE ---

class VectorDBListenerAgent(Agent):
    """A simple listener to verify that processed chunks are being published."""
    def __init__(self, name="VectorDBListener", message_bus=None, config=None):
        super().__init__(name, message_bus, config)
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.PROCESSED_DATA_CHUNKS, self)

    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.PROCESSED_DATA_CHUNKS:
            chunk_count = len(msg.get('chunks', []))
            sample_chunk = msg.get('chunks', [{}])[0]
            print("\n\n=============== ✅ VECTOR DB LISTENER RECEIVED CHUNKS ✅ ===============")
            print(f"  Source Repository: {msg.get('source_repo')}")
            print(f"  Total Chunks Ready for Embedding: {chunk_count}")
            print(f"  SAMPLE CHUNK:")
            print(f"    File: {sample_chunk.get('file_path')}")
            print(f"    Type: {sample_chunk.get('chunk_type')}")
            print(f"    Identifier: {sample_chunk.get('identifier')}")
            print(f"    Content: '{textwrap.shorten(sample_chunk.get('content', ''), 150)}'")
            print("========================================================================\n")


# --- MAIN ORCHESTRATION ---

async def main():
    print("--- Orchestration System with Processing Pipeline Starting ---")
    bus = CentralMessageBus()
    
    # Initialize all our agents
    data_creator = DataCreatorAgent(name="DataCreatorAgent", message_bus=bus)
    processing_agent = ProcessingAgent(name="ProcessingAgent", message_bus=bus)
    vector_db_listener = VectorDBListenerAgent(name="VectorDBListener", message_bus=bus)

    # Register them
    bus.register_agent(data_creator.name, data_creator.inbox)
    bus.register_agent(processing_agent.name, processing_agent.inbox)
    bus.register_agent(vector_db_listener.name, vector_db_listener.inbox)
    
    # Start agent tasks
    agent_tasks = [
        asyncio.create_task(data_creator.run()),
        asyncio.create_task(processing_agent.run()),
        asyncio.create_task(vector_db_listener.run())
    ]
    
    print("\n--- AGENTS ARE LIVE. ISSUING COMMANDS ---\n")
    
    # Send a single, clear task to test the whole pipeline
    DataCreatorAgent(message_bus=bus).send({
        "type": "clone_and_extract_repo", 
        "repo_url": "https://github.com/huggingface/knockknock"
    })

    await asyncio.sleep(20) # Allow time for clone, extract, process

    print("\n--- SHUTTING DOWN AGENTS. ---")
    for task in agent_tasks: task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    print("--- Orchestration System Shutdown. ---")

if __name__ == "__main__":
    asyncio.run(main())