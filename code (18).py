import asyncio
import os
import openai
import textwrap
import json # For writing training data
import uuid # For unique task IDs

# --- BASE CLASSES and UTILITIES (UNCHANGED) ---
class Agent:
    def __init__(self, name="BaseAgent", message_bus=None, config=None):
        self.name = name; self.inbox = []; self.config = config or {}; self.state = "idle"; self.message_bus = message_bus
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
    async def handle_message(self, msg): print(f"Agent '{self.name}' unhandled message: {msg}")

class CentralMessageBus:
    def __init__(self): self._agent_inboxes, self._subscriptions = {}, {}
    def register_agent(self, name, inbox): self._agent_inboxes[name] = inbox
    def subscribe(self, event_type, agent):
        if event_type not in self._subscriptions: self._subscriptions[event_type] = []
        if agent not in self._subscriptions[event_type]: self._subscriptions[event_type].append(agent)
    async def publish(self, message, target=None):
        event_type = message.get('type')
        if target and target in self._agent_inboxes: self._agent_inboxes[target].append(message)
        elif event_type and event_type in self._subscriptions:
            for agent in self._subscriptions[event_type]:
                if hasattr(agent, 'inbox'): agent.inbox.append(message)

# --- AGENT DEFINITIONS ---

class CodeGeneratorAgent(Agent):
    """Generates code and echoes the task_id for correlation."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key: self.state = "error"; print("❌ CodeGeneratorAgent ERROR: OPENAI_API_KEY not set.")
        else: self.client = openai.AsyncOpenAI(api_key=self.api_key)
        if self.message_bus: self.message_bus.subscribe("generate_code", self)

    def _build_prompt(self, msg):
        task = msg.get("task_description", "")
        context_snippets = msg.get("context_snippets", [])
        prompt = f"TASK: {task}\n\n"
        if context_snippets:
            prompt += "Use the following code snippets from the existing codebase as context and reference for style and structure:\n\n"
            for snippet in context_snippets:
                prompt += f"--- CONTEXT FROM: {snippet.get('file_path')} ---\n{snippet.get('content')}\n--- END OF CONTEXT ---\n\n"
        prompt += "Please provide only the complete, final code or analysis as your response."
        return prompt

    async def handle_message(self, msg):
        if self.state == "error": return
        response_agent, task_id = msg.get("response_agent"), msg.get("task_id")
        if not response_agent or not task_id: return
        
        print(f"⏳ CodeGeneratorAgent: Received task {task_id[:8]}...")
        try:
            prompt = self._build_prompt(msg)
            chat_completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": "You are an expert Python software architect."}, {"role": "user", "content": prompt}],
                model="gpt-4-turbo-preview",
            )
            generated_content = chat_completion.choices[0].message.content
            
            self.send({
                "type": "generated_code",
                "task_id": task_id, # Echo the ID back
                "original_task": msg.get("task_description"),
                "prompt": prompt, # Include the full prompt for the collector
                "content": generated_content
            }, target_agent_name=response_agent)
        except Exception as e:
            print(f"❌ CodeGeneratorAgent ERROR: {e}")


# --- NEW AGENT: THE TRAINING DATA COLLECTOR ---

class TrainingDataCollectorAgent(Agent):
    """
    Passively listens to conversations and records high-quality
    prompt/completion pairs to a file for fine-tuning.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_file = self.config.get("output_file", "training_dataset.jsonl")
        self.pending_prompts = {}
        if self.message_bus:
            # Listen for the initial request AND the final response
            self.message_bus.subscribe("generate_code", self)
            self.message_bus.subscribe("generated_code", self)
        print(f"✅ TrainingDataCollectorAgent is online. Recording to '{self.output_file}'.")

    async def handle_message(self, msg):
        task_id = msg.get("task_id")
        if not task_id: return

        # If it's the initial request, store the prompt
        if msg["type"] == "generate_code":
            self.pending_prompts[task_id] = msg
        
        # If it's the final response, find the matching prompt and write the pair
        elif msg["type"] == "generated_code":
            if task_id in self.pending_prompts:
                initial_request = self.pending_prompts.pop(task_id)
                
                # Format for fine-tuning
                training_example = {
                    "messages": [
                        {"role": "system", "content": "You are an expert Python software architect."},
                        {"role": "user", "content": self._build_prompt(initial_request)},
                        {"role": "assistant", "content": msg.get("content")}
                    ]
                }
                
                with open(self.output_file, 'a') as f:
                    f.write(json.dumps(training_example) + '\n')
                
                print(f"✅ TrainingDataCollector: Saved training example for task {task_id[:8]}.")

    def _build_prompt(self, msg): # Helper to reconstruct the exact prompt
        task = msg.get("task_description", "")
        context_snippets = msg.get("context_snippets", [])
        prompt = f"TASK: {task}\n\n"
        if context_snippets:
            prompt += "Use the following code snippets as context:\n\n"
            for snippet in context_snippets:
                prompt += f"--- CONTEXT FROM: {snippet.get('file_path')} ---\n{snippet.get('content')}\n--- END OF CONTEXT ---\n\n"
        prompt += "Please provide only the complete, final code or analysis."
        return prompt

class OrchestratorAgent(Agent):
    """The main coordinator, now creating training data."""
    async def handle_message(self, msg):
        if msg.get("type") == "generated_code":
            print("\n\n=============== 🤖 ORCHESTRATOR RECEIVED GENERATED CODE 🤖 ===============")
            print(f"  Task ID: {msg.get('task_id')}")
            print(f"  Task: {msg.get('original_task')}")
            print("  --- LLM-Generated Content ---")
            print(textwrap.indent(msg.get('content', ''), '    '))
            print("========================================================================\n")
    
    def request_code_generation(self, task_description, context, target_agent="CodeGenerator"):
        """Sends a structured request for code generation."""
        task_id = str(uuid.uuid4())
        print(f"⏳ Orchestrator: Sending task {task_id[:8]} to {target_agent}.")
        self.send({
            "type": "generate_code",
            "task_id": task_id,
            "task_description": task_description,
            "context_snippets": context,
            "response_agent": self.name
        }, target_agent_name=target_agent)

# --- MAIN EXECUTION ---
async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("\n\n❌ FATAL: OPENAI_API_KEY is not set. The system cannot proceed.")
        return

    print("--- System with Self-Improvement Data Collection STARTING ---")
    bus = CentralMessageBus()

    # Initialize all agents
    orchestrator = OrchestratorAgent(name="Orchestrator", message_bus=bus)
    code_generator = CodeGeneratorAgent(name="CodeGenerator", message_bus=bus)
    collector = TrainingDataCollectorAgent(name="Collector", message_bus=bus, config={"output_file": "training_dataset.jsonl"})

    # Register them
    for agent in [orchestrator, code_generator, collector]:
        bus.register_agent(agent.name, agent.inbox)

    tasks = [asyncio.create_task(agent.run()) for agent in [orchestrator, code_generator, collector]]
    await asyncio.sleep(1)

    print("\n--- ORCHESTRATOR INITIATING A TASK ---")
    simulated_context = [
        {"file_path": "knockknock/notifiers.py", "content": "def slack_sender(...): ..."},
        {"file_path": "knockknock/notifiers.py", "content": "def telegram_sender(...): ..."}
    ]
    orchestrator.request_code_generation(
        task_description="Create a new Python function for sending notifications to Microsoft Teams named `teams_sender`.",
        context=simulated_context
    )
    
    await asyncio.sleep(15)

    print("\n--- SHUTTING DOWN ---")
    for task in tasks: task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n--- SYSTEM SHUTDOWN COMPLETE ---")
    if os.path.exists("training_dataset.jsonl"):
        print(f"✅ SUCCESS: A new training dataset has been created at 'training_dataset.jsonl'.")
        print("This file contains the high-quality data needed to fine-tune our own models.")

if __name__ == "__main__":
    asyncio.run(main())