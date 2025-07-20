import logging
from collections import Counter
from super_advanced_agents import (
    FAISSVectorStore, EmbeddingPipeline, LLMGenerator, ContextWindowAgent, HybridScoringAgent
)

logging.basicConfig(level=logging.INFO)

class CollaborationOrchestrator:
    def __init__(self):
        self.agents = {}
        self.logger = logging.getLogger("CollaborationOrchestrator")

    def register_agent(self, name: str, agent):
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")

    def collaborate(self, query: str, agent_names: list, voting: str = "majority", llm_critic=None, **kwargs):
        responses = []
        for name in agent_names:
            agent = self.agents[name]
            if hasattr(agent, "answer"):
                resp = agent.answer(query)
            elif hasattr(agent, "retrieve"):
                resp = agent.retrieve(query, **kwargs)
            elif hasattr(agent, "summarize_memories"):
                resp = agent.summarize_memories(query, **kwargs)
            else:
                resp = None
            responses.append((name, resp))
        if voting == "majority":
            votes = Counter([str(r[1]) for r in responses])
            best = votes.most_common(1)[0][0]
            return {"responses": responses, "winner": best}
        elif voting == "llm_critic" and llm_critic:
            best = llm_critic(query, responses)
            return {"responses": responses, "winner": best}
        else:
            return {"responses": responses}

    def consensus(self, query: str, agent_names: list, **kwargs):
        responses = [self.agents[name].answer(query) for name in agent_names]
        if all(r == responses[0] for r in responses):
            return {"consensus": True, "answer": responses[0]}
        else:
            return {"consensus": False, "answers": responses}

# LLM Critic function
def llm_critic(query, responses, llm_generator):
    prompt = "Given the following question and agent answers, select the best answer and explain why.\n"
    prompt += f"Question: {query}\n"
    for i, (name, resp) in enumerate(responses):
        prompt += f"Agent {name}: {resp}\n"
    prompt += "Best answer:"
    return llm_generator.generate(prompt, max_length=100)

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

    # Collaboration orchestrator setup
    collab = CollaborationOrchestrator()
    collab.register_agent("retriever", retriever)
    collab.register_agent("summarizer", summarizer)
    collab.register_agent("context", context_agent)

    print("\n--- Collaboration: Majority Vote ---")
    result = collab.collaborate("Paris", ["retriever", "summarizer", "context"], voting="majority")
    print(result)

    print("\n--- Collaboration: LLM Critic ---")
    result = collab.collaborate("Paris", ["retriever", "summarizer", "context"], voting="llm_critic", llm_critic=lambda q, rs: llm_critic(q, rs, llm))
    print(result)

    print("\n--- Collaboration: Consensus ---")
    result = collab.consensus("Paris", ["retriever", "summarizer", "context"])
    print(result)