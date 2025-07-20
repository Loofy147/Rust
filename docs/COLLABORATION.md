# Collaboration & Voting

This document describes agent collaboration, voting, and consensus patterns in the Super Advanced Agent Framework.

## CollaborationOrchestrator

Coordinates multiple agents to answer a query, then aggregates responses by majority vote, LLM-based critique, or consensus.

### Initialization
```python
from collaboration_orchestrator import CollaborationOrchestrator
collab = CollaborationOrchestrator()
```

### Registering Agents
```python
collab.register_agent("retriever", retriever)
collab.register_agent("summarizer", summarizer)
collab.register_agent("context", context_agent)
```

### Majority Voting
Each agent answers the query; the most common answer wins.
```python
result = collab.collaborate("Paris", ["retriever", "summarizer", "context"], voting="majority")
print(result["winner"])
```

### LLM Critic
Use an LLM to select and explain the best answer among agent responses.
```python
def llm_critic(query, responses, llm_generator):
    prompt = "Given the following question and agent answers, select the best answer and explain why.\n"
    prompt += f"Question: {query}\n"
    for i, (name, resp) in enumerate(responses):
        prompt += f"Agent {name}: {resp}\n"
    prompt += "Best answer:"
    return llm_generator.generate(prompt, max_length=100)

result = collab.collaborate(
    "Paris", ["retriever", "summarizer", "context"],
    voting="llm_critic", llm_critic=lambda q, rs: llm_critic(q, rs, llm)
)
print(result["winner"])
```

### Consensus
All agents must agree (return the same answer).
```python
result = collab.consensus("Paris", ["retriever", "summarizer", "context"])
if result["consensus"]:
    print("Consensus answer:", result["answer"])
else:
    print("No consensus. Answers:", result["answers"])
```

## Best Practices
- Use majority voting for robustness to outliers.
- Use LLM critic for nuanced or open-ended questions.
- Use consensus for critical tasks requiring agent agreement.
- Log all responses and decisions for auditability.

## Extension Points
- Add weighted voting (e.g., by agent confidence or specialization).
- Use LLMs for critique, explanation, or even to generate new candidate answers.
- Combine with orchestration for multi-stage workflows (e.g., retrieve → vote → summarize).