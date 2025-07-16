import logging
from super_advanced_agents import (
    FAISSVectorStore, EmbeddingPipeline, LLMGenerator, PluginAgent, ContextWindowAgent,
    ExpiryAgent, PersonalizationAgent, ProvenanceAgent, HybridScoringAgent
)

logging.basicConfig(level=logging.INFO)

class Orchestrator:
    def __init__(self):
        self.agents = {}
        self.logger = logging.getLogger("Orchestrator")

    def register_agent(self, name: str, agent):
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")

    def route(self, query: str, user_id: str = None, task: str = None, **kwargs):
        if task == "summarize":
            agent = self.agents.get("summarizer")
            return agent.summarize_memories(query, **kwargs)
        elif task == "retrieve":
            agent = self.agents.get("retriever")
            return agent.retrieve(query, **kwargs)
        elif task == "personal":
            agent = self.agents.get("personalization")
            return agent.search_for_user(query, user_id=user_id, **kwargs)
        elif task == "context":
            agent = self.agents.get("context")
            return agent.answer(query)
        elif task == "plugin":
            agent = self.agents.get("plugin")
            return agent.call_plugin(kwargs.get("plugin_name"), *kwargs.get("plugin_args", []))
        else:
            agent = self.agents.get("hybrid")
            return agent.hybrid_search(query, **kwargs)

    def chain(self, query: str, chain: list, **kwargs):
        result = query
        for agent_name in chain:
            agent = self.agents.get(agent_name)
            if hasattr(agent, "summarize_memories"):
                result = agent.summarize_memories(result, **kwargs)
            elif hasattr(agent, "retrieve"):
                result = agent.retrieve(result, **kwargs)
            elif hasattr(agent, "answer"):
                result = agent.answer(result)
            else:
                result = agent(result)
        return result

    def supervise(self):
        for name, agent in self.agents.items():
            if hasattr(agent, "get_memory_stats"):
                stats = agent.get_memory_stats()
                self.logger.info(f"Agent {name} stats: {stats}")

    def fallback(self, query: str, primary: str, backup: str, **kwargs):
        try:
            agent = self.agents[primary]
            return agent.retrieve(query, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary agent {primary} failed: {e}, using backup {backup}")
            agent = self.agents[backup]
            return agent.retrieve(query, **kwargs)

if __name__ == "__main__":
    # Instantiate shared resources and agents as in super_advanced_agents.py
    store = FAISSVectorStore(dim=384)
    embedder = EmbeddingPipeline()
    llm = LLMGenerator()

    # Populate store with some facts
    facts = [
        ("The Eiffel Tower is in Paris.", "fact", "eiffel"),
        ("The Louvre is a famous museum.", "fact", "louvre"),
        ("Berlin has the Brandenburg Gate.", "fact", "berlin"),
        ("The Colosseum is in Rome.", "fact", "colosseum"),
        ("Paris is known for its cafes.", "fact", "paris_cafe"),
    ]
    for text, typ, uid in facts:
        store.add(embedder.embed(text), {"text": text, "type": typ}, uid)

    # Instantiate agents
    retriever = HybridScoringAgent("HybridRetriever", store, embedder, llm)
    summarizer = ContextWindowAgent("Summarizer", store, embedder, llm, max_context=200)
    context_agent = ContextWindowAgent("Context", store, embedder, llm, max_context=200)
    pers_agent = PersonalizationAgent("Personal", store, embedder)
    plugin_agent = PluginAgent("Plugin", store, embedder)
    plugin_agent.register_plugin("add", lambda x, y: x + y)
    hybrid_agent = HybridScoringAgent("Hybrid", store, embedder, llm)

    # Add user memories for personalization
    pers_agent.add_user_memory("User1's secret", user_id="user1")
    pers_agent.add_user_memory("User2's secret", user_id="user2")

    # Orchestrator setup
    orchestrator = Orchestrator()
    orchestrator.register_agent("retriever", retriever)
    orchestrator.register_agent("summarizer", summarizer)
    orchestrator.register_agent("context", context_agent)
    orchestrator.register_agent("personalization", pers_agent)
    orchestrator.register_agent("plugin", plugin_agent)
    orchestrator.register_agent("hybrid", hybrid_agent)

    print("\n--- Orchestrator: Route to Summarizer ---")
    print(orchestrator.route("Paris", task="summarize", top_k=3))

    print("\n--- Orchestrator: Chain Retrieve → Summarize ---")
    print(orchestrator.chain("museum", ["retriever", "summarizer"], top_k=3))

    print("\n--- Orchestrator: Route to PersonalizationAgent ---")
    print(orchestrator.route("secret", user_id="user1", task="personal"))

    print("\n--- Orchestrator: Fallback from Retriever to Hybrid ---")
    print(orchestrator.fallback("museum", primary="retriever", backup="hybrid", top_k=2))

    print("\n--- Orchestrator: Supervise Agents ---")
    orchestrator.supervise()