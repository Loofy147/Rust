import streamlit as st
import requests
import time

API_URL = "http://localhost:8000"  # Adjust as needed

st.title("Distributed Agent System Dashboard")

# --- Nodes ---
st.header("Nodes/Agents")
if st.button("Refresh Nodes"):
    nodes = requests.get(f"{API_URL}/agents/nodes").json()
    st.write(nodes)

# --- Plugins ---
st.header("Plugins")
if st.button("List Plugins"):
    plugins = requests.get(f"{API_URL}/plugins").json()
    st.write(plugins)

with st.form("Load Plugin"):
    module = st.text_input("Module", "plugins.normalizer_plugin")
    cls = st.text_input("Class", "NormalizerPlugin")
    submitted = st.form_submit_button("Load Plugin")
    if submitted:
        r = requests.post(f"{API_URL}/plugins/load", json={"module": module, "class": cls})
        st.write(r.json())

with st.form("Unload Plugin"):
    cls = st.text_input("Class to Unload", "NormalizerPlugin")
    submitted = st.form_submit_button("Unload Plugin")
    if submitted:
        r = requests.post(f"{API_URL}/plugins/unload", json={"class": cls})
        st.write(r.json())

# --- Tasks ---
st.header("Tasks")
if st.button("Show All Results"):
    results = requests.get(f"{API_URL}/tasks/results").json()
    st.write(results)

with st.form("Assign Task"):
    node_id = st.text_input("Node ID", "node-1")
    text = st.text_input("Task Text", "Hello distributed world!")
    submitted = st.form_submit_button("Assign Task")
    if submitted:
        task = {"id": int(time.time()), "text": text}
        r = requests.post(f"{API_URL}/tasks/assign", json={"node_id": node_id, "task": task})
        st.write(r.json())