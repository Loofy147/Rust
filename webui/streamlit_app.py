import streamlit as st
import requests
import time
import json
import threading
import websocket

API_URL = st.secrets["API_URL"] if "API_URL" in st.secrets else "http://localhost:8000"

st.title("ReasoningAgent Web UI")

# --- Auth ---
st.sidebar.header("Authentication")
auth_method = st.sidebar.radio("Auth Method", ["API Key", "JWT Login"], horizontal=True)
api_key = ""
jwt_token = ""

if auth_method == "API Key":
    api_key = st.sidebar.text_input("API Key", type="password")
else:
    username = st.sidebar.text_input("Username", value="admin")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        resp = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
        if resp.status_code == 200:
            jwt_token = resp.json()["access_token"]
            st.session_state["jwt_token"] = jwt_token
            st.sidebar.success("Logged in!")
        else:
            st.sidebar.error("Login failed")
    jwt_token = st.session_state.get("jwt_token", "")

headers = {}
if api_key:
    headers["x-api-key"] = api_key
elif jwt_token:
    headers["Authorization"] = f"Bearer {jwt_token}"

# --- Task Submission ---
st.header("Submit a Task")
task_input = st.text_area("Task Input", max_chars=2048)
if st.button("Submit Task"):
    if not headers:
        st.error("Please authenticate first.")
    elif not task_input.strip():
        st.error("Task input cannot be empty.")
    else:
        resp = requests.post(f"{API_URL}/tasks", json={"input": task_input}, headers=headers)
        if resp.status_code == 200:
            task_id = resp.json()["id"]
            st.session_state["last_task_id"] = task_id
            st.success(f"Task submitted! Task ID: {task_id}")
        else:
            st.error(f"Error: {resp.text}")

# --- Task Status/Result ---
if "last_task_id" in st.session_state:
    task_id = st.session_state["last_task_id"]
    st.header(f"Task Status: {task_id}")
    status_placeholder = st.empty()
    result_placeholder = st.empty()

    def ws_status():
        ws_url = API_URL.replace("http", "ws") + f"/ws/tasks/{task_id}"
        try:
            ws = websocket.create_connection(ws_url)
            while True:
                msg = ws.recv()
                data = json.loads(msg)
                if "error" in data:
                    status_placeholder.error(f"WebSocket error: {data['error']}")
                    break
                status_placeholder.info(f"Status: {data['status']}")
                if data["result"]:
                    result_placeholder.code(data["result"])
                    break
        except Exception as e:
            status_placeholder.warning(f"WebSocket failed: {e}. Falling back to polling.")
            poll_status()

    def poll_status():
        while True:
            resp = requests.get(f"{API_URL}/tasks/{task_id}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                status_placeholder.info(f"Status: {data['status']}")
                if data["result"]:
                    result_placeholder.code(data["result"])
                    break
            else:
                status_placeholder.error(f"Error: {resp.text}")
                break
            time.sleep(2)

    st.button("Refresh Status", on_click=poll_status)
    if st.button("Start Live Updates (WebSocket)"):
        threading.Thread(target=ws_status, daemon=True).start()
    if st.button("Start Live Polling"):
        threading.Thread(target=poll_status, daemon=True).start()