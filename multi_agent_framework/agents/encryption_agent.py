try:
    from cryptography.fernet import Fernet
except ImportError:
    raise ImportError("The 'cryptography' library is required for the EncryptionAgent. Please install it with 'pip install cryptography'.")

from .base import Agent

class EncryptionAgent(Agent):
    """
    An agent for encrypting and decrypting data.
    """
    def __init__(self, name, store, embedder, llm=None):
        super().__init__(name, store, embedder, llm)
        # In a real application, the key would be fetched from a secure key management
        # service like HashiCorp Vault or AWS KMS. For this example, we'll generate
        # a key and store it in memory.
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data):
        """
        Encrypts data.
        """
        if not isinstance(data, bytes):
            data = str(data).encode()
        return self.fernet.encrypt(data)

    def decrypt(self, encrypted_data):
        """
        Decrypts data.
        """
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return decrypted_data.decode()
