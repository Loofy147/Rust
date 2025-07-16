from agents.base import BaseAgent
import os

class LLMReasoningAgent(BaseAgent):
    def __init__(self, agent_id, registry, model='gpt-3.5-turbo'):
        super().__init__(agent_id, registry)
        self.skills = ['llm_reasoning']
        self.model = model
        self.api_key = os.environ.get('OPENAI_API_KEY')

    def process(self, task):
        question = task.get('question')
        context = task.get('context', '')
        feedback = task.get('feedback', '')
        prompt = self._build_prompt(question, context, feedback)
        answer, rationale, needs_clarification = self._call_llm(prompt)
        return {
            'answer': answer,
            'rationale': rationale,
            'needs_clarification': needs_clarification
        }

    def _build_prompt(self, question, context, feedback):
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n"
        if feedback:
            prompt += f"\nPrevious feedback: {feedback}\n"
        prompt += "\nPlease answer the question, provide your reasoning, and if the question is ambiguous, ask a clarifying question."
        return prompt

    def _call_llm(self, prompt):
        # For demo: stub, replace with OpenAI/HF API call
        # In production, use openai.ChatCompletion.create or transformers pipeline
        if 'ambiguous' in prompt.lower():
            return (None, None, 'Can you clarify your question?')
        answer = "This is a grounded, reasoned answer."
        rationale = "I used the provided context and my domain knowledge."
        return (answer, rationale, None)