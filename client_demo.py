import requests
import time
import yaml
from plugins.vectorizer_plugin import VectorizerPlugin

# Load config for API details and auth
with open('config.yaml') as f:
    config = yaml.safe_load(f)

API_URL = f"http://{config['api']['host']}:{config['api']['port']}"
AUTH = {"Authorization": f"Bearer {config['api']['auth_token']}"}

# 1. Submit tasks
texts = [
    "The quick brown fox jumps over the lazy dog.",
    "A fast, dark fox leaps above a sleepy canine.",
    "Artificial intelligence is transforming the world.",
    "Machine learning and deep learning are subsets of AI.",
    "The sun rises in the east and sets in the west."
]

for text in texts:
    task = {"type": "process", "text": text}
    r = requests.post(f"{API_URL}/data", headers=AUTH, json=task)
    print(f"Submitted: {text} | Status: {r.json()}")

# 2. Wait for processing (simulate)
time.sleep(5)

# 3. Retrieve all data
data = requests.get(f"{API_URL}/data", headers=AUTH).json()
print(f"\nAll processed data:")
for item in data:
    print(item)

# 4. Vector search for a query
query_text = "A fox jumps over a dog."
vectorizer = VectorizerPlugin(config['plugins']['vectorizer'])
query_vector = vectorizer.run(query_text)
search_payload = {"vector": query_vector, "k": 3}
search_results = requests.post(f"{API_URL}/vector_search", headers=AUTH, json=search_payload).json()
print(f"\nVector search results for: '{query_text}'")
for res in search_results.get("results", []):
    print(res)