import asyncio
import os
import logging
import time
import json
import re
import fnmatch
import textwrap
import ast
from datetime import datetime
import subprocess
import shutil
import random

# --- CRITICAL NEW IMPORTS for VectorDBAgent ---
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

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
    REPO_DATA_EXTRACTED = "repo_data_extracted"
    PROCESSED_DATA_CHUNKS = "processed_data_chunks"
    QUERY_VECTOR_DB = "query_vector_db"
    QUERY_RESULT = "query_result" # New event for sending results back

def extract_repo_data(repo_path, include_patterns=['*.py', '*.md'], exclude_patterns=['.git/*']):
    # This function remains the same as before
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

# --- AGENT PIPELINE DEFINITIONS ---

class DataCreatorAgent(Agent):
    """Clones repos and publishes raw file data."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clone_dir = self.config.get("clone_dir", "./cloned_repos")
        os.makedirs(self.clone_dir, exist_ok=True)
        if self.message_bus: self.message_bus.subscribe("clone_and_extract_repo", self)

    async def handle_message(self, msg):
        repo_url = msg.get("repo_url")
        if not repo_url or self.state == "processing": return
        self.state = "processing"
        local_repo_path = os.path.join(self.clone_dir, repo_url.split('/')[-1])
        try:
            print(f"\n⏳ DataCreatorAgent: Cloning '{repo_url}'")
            await asyncio.to_thread(lambda: (shutil.rmtree(local_repo_path, ignore_errors=True), subprocess.run(['git', 'clone', '--depth', '1', repo_url, local_repo_path], check=True, capture_output=True)))
            extracted_data = extract_repo_data(local_repo_path)
            if extracted_data: self.send({"type": ArchitectureEventType.REPO_DATA_EXTRACTED, "source_repo": repo_url, "data": extracted_data})
        except Exception as e: print(f"❌ DataCreatorAgent ERROR: {e}")
        finally:
            shutil.rmtree(local_repo_path, ignore_errors=True)
            self.state = "idle"

class ProcessingAgent(Agent):
    """Chunks raw data using AST for code and text splitters for markdown."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.message_bus: self.message_bus.subscribe(ArchitectureEventType.REPO_DATA_EXTRACTED, self)

    async def handle_message(self, msg):
        if msg.get("type") != ArchitectureEventType.REPO_DATA_EXTRACTED: return
        print(f"⏳ ProcessingAgent: Chunking {len(msg.get('data',[]))} files...")
        all_chunks = [chunk for file_data in msg.get('data', []) for chunk in self._process_file(file_data, msg.get('source_repo'))]
        if all_chunks:
            print(f"✅ ProcessingAgent: Generated {len(all_chunks)} chunks.")
            self.send({"type": ArchitectureEventType.PROCESSED_DATA_CHUNKS, "source_repo": msg.get('source_repo'), "chunks": all_chunks})

    def _process_file(self, file_data, repo_name):
        path, content = file_data.get('file_path'), file_data.get('content')
        if path.endswith('.py'): return self._chunk_python(content, path, repo_name)
        return [] # Can add markdown/text chunkers here

    def _chunk_python(self, content, path, repo):
        chunks = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    chunk_content = ast.get_source_segment(content, node)
                    if chunk_content: chunks.append({"repo_name": repo, "file_path": path, "type": type(node).__name__, "identifier": node.name, "content": chunk_content})
        except Exception: pass
        return chunks

# --- NEW AGENT: THE VECTOR DATABASE AGENT ---

class VectorDBAgent(Agent):
    """Indexes data chunks and handles semantic search queries."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("⏳ VectorDBAgent: Initializing... This may take a moment.")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)
        self.doc_store = []
        if self.message_bus:
            self.message_bus.subscribe(ArchitectureEventType.PROCESSED_DATA_CHUNKS, self)
            self.message_bus.subscribe(ArchitectureEventType.QUERY_VECTOR_DB, self)
        print("✅ VectorDBAgent: Online and ready to index or query.")

    async def handle_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == ArchitectureEventType.PROCESSED_DATA_CHUNKS:
            await self._handle_indexing(msg)
        elif msg_type == ArchitectureEventType.QUERY_VECTOR_DB:
            await self._handle_query(msg)

    async def _handle_indexing(self, msg):
        chunks = msg.get("chunks", [])
        if not chunks: return
        
        print(f"⏳ VectorDBAgent: Received {len(chunks)} chunks. Generating embeddings...")
        contents = [chunk['content'] for chunk in chunks]
        embeddings = await asyncio.to_thread(self.model.encode, contents)
        
        self.index.add(np.array(embeddings))
        self.doc_store.extend(chunks)
        print(f"✅ VectorDBAgent: Successfully indexed {len(chunks)} chunks. Total indexed: {self.index.ntotal}")

    async def _handle_query(self, msg):
        query, k, response_agent = msg.get("query"), msg.get("k", 3), msg.get("response_agent")
        if not query or not response_agent: return

        print(f"⏳ VectorDBAgent: Searching for '{query}'...")
        query_embedding = await asyncio.to_thread(self.model.encode, [query])
        distances, indices = self.index.search(np.array(query_embedding), k)
        
        results = [self.doc_store[i] for i in indices[0]]
        print(f"✅ VectorDBAgent: Found {len(results)} results. Sending to '{response_agent}'.")
        self.send({
            "type": ArchitectureEventType.QUERY_RESULT,
            "query": query,
            "results": results
        }, target_agent_name=response_agent)

# --- UPGRADED ORCHESTRATOR AGENT ---
class OrchestratorAgent(Agent):
    """The main coordinator, now capable of initiating tasks and processing results."""
    async def handle_message(self, msg):
        if msg.get("type") == ArchitectureEventType.QUERY_RESULT:
            print("\n\n=============== 🧠 ORCHESTRATOR RECEIVED QUERY RESULTS 🧠 ===============")
            print(f"  Query: '{msg.get('query')}'")
            print("  --- Top 3 Most Relevant Code Chunks ---")
            for i, result in enumerate(msg.get('results', [])):
                print(f"\n  {i+1}. From File: {result.get('file_path')} (Function/Class: {result.get('identifier')})")
                print(textwrap.indent(textwrap.shorten(result.get('content'), 300), '     '))
            print("========================================================================\n")

# --- MAIN EXECUTION ---
async def main():
    print("--- FULL PIPELINE (CREATE -> PROCESS -> INDEX -> QUERY) STARTING ---")
    print("--- NOTE: First run will download embedding model (~23MB) ---")
    bus = CentralMessageBus()
    
    # Initialize all agents in the pipeline
    orchestrator = OrchestratorAgent(name="Orchestrator", message_bus=bus)
    data_creator = DataCreatorAgent(name="DataCreator", message_bus=bus)
    processing_agent = ProcessingAgent(name="Processor", message_bus=bus)
    vector_db_agent = VectorDBAgent(name="VectorDB", message_bus=bus)

    # Register agents that need to be messaged directly or subscribed
    for agent in [orchestrator, data_creator, processing_agent, vector_db_agent]:
        bus.register_agent(agent.name, agent.inbox)
    
    tasks = [asyncio.create_task(agent.run()) for agent in [orchestrator, data_creator, processing_agent, vector_db_agent]]
    
    await asyncio.sleep(2) # Allow agents to initialize, especially the model download
    
    print("\n--- AGENTS ARE LIVE. ORCHESTRATOR ISSUING COMMANDS ---")
    
    # Step 1: Ingest a repository
    orchestrator.send({"type": "clone_and_extract_repo", "repo_url": "https://github.com/huggingface/knockknock"}, "DataCreator")
    
    # Wait for the pipeline to process the data
    print("\n--- Waiting for ingestion and indexing to complete... ---")
    await asyncio.sleep(20)
    
    # Step 2: Query the knowledge base
    print("\n--- INGESTION COMPLETE. NOW, LET'S QUERY THE KNOWLEDGE! ---")
    orchestrator.send({
        "type": ArchitectureEventType.QUERY_VECTOR_DB,
        "query": "How do I send a notification to Slack?",
        "k": 3,
        "response_agent": "Orchestrator"
    }, "VectorDB")

    await asyncio.sleep(5)

    print("\n--- SHUTTING DOWN AGENTS. ---")
    for task in tasks: task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("--- ORCHESTRATION COMPLETE. ---")

if __name__ == "__main__":
    # Remember to run: pip install sentence-transformers faiss-cpu numpy
    asyncio.run(main())