import asyncio
import os
import openai # New import
import textwrap

# ... (All previous agent and class definitions remain the same) ...

# --- Placeholder for all the classes defined previously ---
# Agent, CentralMessageBus, ArchitectureEventType, DataCreatorAgent,
# ProcessingAgent, VectorDBAgent, OrchestratorAgent
# We will just define the new agent and update the main orchestration.

class CodeGeneratorAgent(Agent):
    """
    Uses a Large Language Model to generate code or analysis based on
    a structured prompt from the Orchestrator.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # IMPORTANT: Set your API key as an environment variable
        # For example: export OPENAI_API_KEY='sk-...'
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("❌ CodeGeneratorAgent ERROR: OPENAI_API_KEY environment variable not set.")
            self.state = "error"
        else:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            print("✅ CodeGeneratorAgent: Online and ready to generate.")

        if self.message_bus:
            self.message_bus.subscribe("generate_code", self)
            self.message_bus.subscribe("generate_analysis", self)

    async def handle_message(self, msg):
        if self.state == "error":
            return

        response_agent = msg.get("response_agent")
        if not response_agent:
            return

        print(f"⏳ CodeGeneratorAgent: Received task. Generating response for '{response_agent}'...")
        try:
            prompt = self._build_prompt(msg)
            
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert software architect and Python programmer. You write clean, efficient, and well-documented code."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4-turbo-preview", # Or gpt-3.5-turbo
            )
            generated_content = chat_completion.choices[0].message.content
            
            print(f"✅ CodeGeneratorAgent: Generation complete.")
            self.send({
                "type": "generated_code", # Or another appropriate type
                "original_task": msg.get("task_description"),
                "content": generated_content
            }, target_agent_name=response_agent)

        except Exception as e:
            error_message = f"Failed to generate content: {e}"
            print(f"❌ CodeGeneratorAgent ERROR: {error_message}")
            self.send({"type": "error", "details": error_message}, target_agent_name=response_agent)

    def _build_prompt(self, msg):
        """Constructs a detailed prompt for the LLM."""
        task = msg.get("task_description", "Perform the requested action.")
        context_snippets = msg.get("context_snippets", [])

        prompt = f"TASK: {task}\n\n"

        if context_snippets:
            prompt += "Use the following code snippets from the existing codebase as context and reference for style and structure:\n\n"
            for snippet in context_snippets:
                prompt += f"--- CONTEXT FROM: {snippet.get('file_path')} ---\n"
                prompt += f"{snippet.get('content')}\n"
                prompt += f"--- END OF CONTEXT ---\n\n"
        
        prompt += "Please provide only the complete, final code or analysis as your response."
        return prompt

# --- MAIN ORCHESTRATION (SIMPLIFIED FOR DEMONSTRATION) ---
# A full run would involve all agents. For clarity, we will simulate
# the Orchestrator's behavior after it has already received context
# from the VectorDBAgent.

async def main_demo():
    print("--- DEMO: Orchestrator using CodeGeneratorAgent ---")
    bus = CentralMessageBus()

    # The Orchestrator will receive the final result
    class DemoOrchestrator(Agent):
        async def handle_message(self, msg):
            print("\n\n=============== 🤖 ORCHESTRATOR RECEIVED GENERATED CODE 🤖 ===============")
            print(f"  ORIGINAL TASK: {msg.get('original_task')}")
            print("  --- LLM-Generated Content ---")
            print(textwrap.indent(msg.get('content', 'No content received.'), '    '))
            print("========================================================================\n")

    orchestrator = DemoOrchestrator(name="Orchestrator", message_bus=bus)
    code_generator = CodeGeneratorAgent(name="CodeGenerator", message_bus=bus)

    bus.register_agent(orchestrator.name, orchestrator.inbox)
    bus.register_agent(code_generator.name, code_generator.inbox)

    tasks = [
        asyncio.create_task(orchestrator.run()),
        asyncio.create_task(code_generator.run())
    ]
    
    await asyncio.sleep(1)
    
    # This simulates the Orchestrator having ALREADY queried the VectorDB
    # and received these two functions as context.
    simulated_context = [
        {"file_path": "knockknock/notifiers.py", "content": "def slack_sender(webhook_url: str, channel: str, message: str): ..."},
        {"file_path": "knockknock/notifiers.py", "content": "def telegram_sender(token: str, chat_id: int, message: str): ..."}
    ]

    # The Orchestrator now sends the complete, structured task to the CodeGenerator
    orchestrator.send({
        "type": "generate_code",
        "task_description": "Create a new Python function for sending notifications to Microsoft Teams. It should take a `webhook_url` and a `message`. The function name should be `teams_sender`. Use the `requests` library.",
        "context_snippets": simulated_context,
        "response_agent": "Orchestrator"
    }, "CodeGenerator")

    # Let it run for a bit to get the result from the API
    await asyncio.sleep(15)

    print("--- SHUTTING DOWN ---")
    for task in tasks: task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    # Ensure you have run:
    # pip install openai sentence-transformers faiss-cpu numpy
    # And set your API key:
    # export OPENAI_API_KEY='sk-...'
    
    # We run the demo function to test the new agent directly.
    # To run the full pipeline, you would integrate this agent
    # into the main script from the previous step.
    if not os.getenv("OPENAI_API_KEY"):
        print("\n\nWARNING: OPENAI_API_KEY is not set. The demo will fail.")
        print("Please set it and run the script again.")
    else:
        asyncio.run(main_demo())