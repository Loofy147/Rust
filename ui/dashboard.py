import streamlit as st
import requests
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

API_URL = f"http://{config['api']['host']}:{config['api']['port']}"
AUTH = {"Authorization": f"Bearer {config['api']['auth_token']}"}

st.title("Agent System Dashboard")

# Health
health = requests.get(f"{API_URL}/health").json()
st.metric("System Health", health['status'])

# Data
if st.button("Refresh Data"):
    data = requests.get(f"{API_URL}/data", headers=AUTH).json()
    st.write(data)

# Add Task (example)
new_task = st.text_input("Add Task")
if st.button("Submit Task"):
    requests.post(f"{API_URL}/data", headers=AUTH, json={"task": new_task})
    st.success("Task submitted!")