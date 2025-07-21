import unittest
from multi_agent_framework.agents.rbac_agent import RBACAgent
from multi_agent_framework.agents.encryption_agent import EncryptionAgent

class TestSecurity(unittest.TestCase):

    def test_rbac_agent(self):
        rbac_agent = RBACAgent("RBAC", None, None)
        rbac_agent.assign_role("user1", "admin")
        self.assertTrue(rbac_agent.check_permission("user1", "read"))
        self.assertTrue(rbac_agent.check_permission("user1", "write"))
        self.assertTrue(rbac_agent.check_permission("user1", "delete"))
        self.assertTrue(rbac_agent.check_permission("user1", "admin"))
        self.assertFalse(rbac_agent.check_permission("user2", "write"))

    def test_encryption_agent(self):
        encryption_agent = EncryptionAgent("Encryption", None, None)
        data = "This is a secret message."
        encrypted_data = encryption_agent.encrypt(data)
        decrypted_data = encryption_agent.decrypt(encrypted_data)
        self.assertEqual(data, decrypted_data)

if __name__ == '__main__':
    unittest.main()
