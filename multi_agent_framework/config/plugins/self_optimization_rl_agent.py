import time
import numpy as np
import random
import pickle
import os

class SelfOptimizationRLAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["self_optimization", "monitoring", "scaling", "rl"]
        self.registry.register(agent_id, {"skills": self.skills})
        self.q_table = {}  # (state, action) -> value
        self.actions = ["scale_up", "scale_down", "redeploy", "noop"]
        self.epsilon = 0.1  # exploration rate
        self.alpha = 0.5    # learning rate
        self.gamma = 0.9    # discount factor
        self.last_state = None
        self.last_action = None
        self.last_time = time.time()
        self.q_save_path = os.environ.get("RL_Q_TABLE_PATH", "/tmp/selfopt_q.pkl")
        self._load_q_table()

    def _state_key(self, metrics):
        # Discretize for Q-table (for demo; use NN for continuous)
        return tuple(
            (int(m.get("load", 0) * 5), int(m.get("errors", 0) > 2))
            for m in metrics.values()
        )

    def _choose_action(self, state):
        if random.random() < self.epsilon or state not in self.q_table:
            return random.choice(self.actions)
        return max(self.q_table[state], key=self.q_table[state].get)

    def _update_q(self, prev_state, action, reward, next_state):
        if prev_state not in self.q_table:
            self.q_table[prev_state] = {a: 0.0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.actions}
        best_next = max(self.q_table[next_state].values())
        old = self.q_table[prev_state][action]
        self.q_table[prev_state][action] = old + self.alpha * (reward + self.gamma * best_next - old)
        self._save_q_table()

    def _save_q_table(self):
        try:
            with open(self.q_save_path, "wb") as f:
                pickle.dump(self.q_table, f)
        except Exception:
            pass

    def _load_q_table(self):
        try:
            if os.path.exists(self.q_save_path):
                with open(self.q_save_path, "rb") as f:
                    self.q_table = pickle.load(f)
        except Exception:
            pass

    def process(self, task):
        metrics = task.get("metrics", {})
        state = self._state_key(metrics)
        action = self._choose_action(state)
        # For demo: reward = -max error - abs(load-0.5) (encourage balanced, low-error)
        reward = -max([m.get("errors", 0) for m in metrics.values()] + [0]) - np.mean([abs(m.get("load", 0) - 0.5) for m in metrics.values()])
        if self.last_state is not None and self.last_action is not None:
            self._update_q(self.last_state, self.last_action, reward, state)
        self.last_state = state
        self.last_action = action
        self.last_time = time.time()
        # Suggest action for each agent (for demo, same action for all)
        suggestions = []
        for agent_id in metrics:
            if action != "noop":
                suggestions.append({"action": action, "agent_id": agent_id})
        return {"timestamp": time.time(), "suggestions": suggestions, "reward": reward}