class StorageBackend:
    def save(self, data):
        raise NotImplementedError
    def load(self):
        raise NotImplementedError

def get_storage_backend(config):
    if config['type'] == 'file':
        from .file_storage import FileStorageBackend
        return FileStorageBackend(config['file_path'])
    if config['type'] == 'vector_db':
        from .vector_db_storage import VectorDBStorageBackend
        return VectorDBStorageBackend(config)
    # Add vector DB or other backends as needed
    raise ValueError(f"Unknown storage type: {config['type']}")