import streamlit as st
import requests
import time

API_URL = "http://localhost:8000"  # Adjust as needed

st.title("Distributed Agent System Dashboard (DB-backed)")

st.header("Nodes/Agents")
if st.button("Refresh Nodes"):
    nodes = requests.get(f"{API_URL}/agents/nodes").json()
    st.write(nodes)
    for nid, info in nodes.items():
        st.write(f"Node: {nid}")
        st.write(f"  Status: {info.get('status')}")
        st.write(f"  Capabilities: {info.get('capabilities', {})}")
        st.write(f"  Load: {info.get('load', 0)}")
        st.write(f"  Last seen: {info.get('last_seen_delta', 0):.1f}s ago")

st.header("Queued Tasks")
if st.button("Show Queued Tasks"):
    queued = requests.get(f"{API_URL}/tasks/queued").json()
    st.write(queued)

st.header("In Progress Tasks")
if st.button("Show In Progress"):
    in_progress = requests.get(f"{API_URL}/tasks/in_progress").json()
    st.write(in_progress)

st.header("Results")
if st.button("Show All Results"):
    results = requests.get(f"{API_URL}/tasks/results").json()
    st.write(results)

with st.form("Submit Task"):
    text = st.text_input("Task Text", "Hello distributed world!")
    required = st.text_area("Required Capabilities (JSON)", "{}")
    submitted = st.form_submit_button("Submit Task")
    if submitted:
        try:
            req = eval(required)
        except Exception:
            req = {}
        payload = {"text": text, "required": req}
        r = requests.post(f"{API_URL}/tasks/submit", json=payload)
        st.write(r.json())