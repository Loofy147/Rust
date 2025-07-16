import pickle
import os

class FileStorageBackend:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = []
        if os.path.exists(self.file_path):
            self.load()

    def save(self, item):
        self.data.append(item)
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.data, f)

    def load(self):
        with open(self.file_path, 'rb') as f:
            self.data = pickle.load(f)
        return self.data