from .base import Agent

class RBACAgent(Agent):
    """
    An agent for managing Role-Based Access Control (RBAC).
    """
    def __init__(self, name, store, embedder, llm=None):
        super().__init__(name, store, embedder, llm)
        # In a real application, roles and permissions would be loaded from a database
        # or a configuration file. For this example, we'll use a simple in-memory dictionary.
        self.roles = {
            "admin": {"permissions": ["read", "write", "delete", "admin"]},
            "user": {"permissions": ["read", "write"]},
            "guest": {"permissions": ["read"]},
        }
        self.user_roles = {}

    def assign_role(self, user_id, role):
        """
        Assigns a role to a user.
        """
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}")
        self.user_roles[user_id] = role
        return f"Role '{role}' assigned to user '{user_id}'."

    def check_permission(self, user_id, permission):
        """
        Checks if a user has a specific permission.
        """
        role = self.user_roles.get(user_id)
        if not role:
            return False
        return permission in self.roles[role]["permissions"]
