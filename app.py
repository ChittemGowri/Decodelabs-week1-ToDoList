"""
SmartTask AI — DecodeLabs Internship 2026
Chittem Gowri Shankar | Viswam Engineering College, JNTUA
"""
import streamlit as st
import plotly.graph_objects as go
import json
import os
import requests
from datetime import datetime, date
from collections import Counter

# --- Setup & Configuration ---
st.set_page_config(page_title="SmartTask AI", page_icon="🧠", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "tasks.json")

PRI_ICON = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}
PRI_NAME = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}

# --- Data Handling Functions ---
def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def is_overdue(task):
    return not task["done"] and bool(task["due"]) and date.fromisoformat(task["due"]) < date.today()

def days_left(task):
    if not task["due"]:
        return None
    return (date.fromisoformat(task["due"]) - date.today()).days

# --- AI Integration ---
def nvidia_ai_call(api_key, prompt, system_prompt="You are a helpful assistant. Be concise.", max_tokens=400):
    try:
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": max_tokens
            },
            timeout=25
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please try again."
    except Exception as e:
        return f"⚠️ API error: {e}"

# --- State Management ---
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

tasks = st.session_state.tasks

# --- UI Header ---
st.title("🧠 SmartTask AI")
st.caption("DecodeLabs Internship 2026 · Chittem Gowri Shankar · Powered by NVIDIA NIM")
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("Settings & Summary")
    api_key = st.text_input("🔑 NVIDIA API Key", type="password", placeholder="nvapi-...")
    st.caption("[Get your key here](https://build.nvidia.com)")
    
    st.divider()
    
    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t["done"])
    overdue_tasks = sum(1 for t in tasks if is_overdue(t))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", total_tasks)
    col2.metric("Done", done_tasks)
    col3.metric("Overdue", overdue_tasks)
    
    if total_tasks > 0:
        st.progress(done_tasks / total_tasks, text=f"{done_tasks / total_tasks:.0%} complete")
        
    st.divider()
    view_filter = st.radio("Task View", ["All", "Pending", "Overdue", "Done"])

# --- Main Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📋 Task List", "➕ Add Task", "🤖 AI Coach", "📊 Statistics"])

# --- TAB 1: Tasks ---
with tab1:
    pool = tasks
    if view_filter == "Pending":
        pool = [t for t in tasks if not t["done"]]
    elif view_filter == "Overdue":
        pool = [t for t in tasks if is_overdue(t)]
    elif view_filter == "Done":
        pool = [t for t in tasks if t["done"]]
        
    # Sort: Highest priority first, then closest due date
    pool = sorted(pool, key=lambda t: (-t["priority"], t["due"] or "9999"))

    search_query = st.text_input("🔍 Search Tasks", placeholder="Type a keyword...")
    if search_query:
        pool = [t for t in pool if search_query.lower() in t["desc"].lower()]

    if not pool:
        st.info(f"No tasks found in the '{view_filter}' view.")

    for t in pool:
        with st.container(border=True):
            d_left = days_left(t)
            badge_text = "No date"
            
            if t["due"]:
                if is_overdue(t):
                    badge_text = f"🚨 Overdue by {-d_left} days"
                elif d_left == 0:
                    badge_text = "🔔 Due TODAY"
                elif d_left <= 3:
                    badge_text = f"⏳ Due in {d_left} days"
                else:
                    badge_text = f"📅 {t['due']}"

            status_icon = "✅" if t["done"] else "⬜"
            
            c_main, c_actions = st.columns([7, 3])
            
            with c_main:
                if t["done"]:
                    st.markdown(f"~~**[#{t['id']}] {t['desc']}**~~")
                else:
                    st.markdown(f"**[#{t['id']}] {t['desc']}**")
                st.caption(f"{PRI_ICON[t['priority']]} Priority: {PRI_NAME[t['priority']]} | {badge_text}")

            with c_actions:
                a1, a2, a3 = st.columns(3)
                if not t["done"]:
                    if a1.button("✅", help="Mark Done", key=f"d_{t['id']}"):
                        for x in tasks:
                            if x["id"] == t["id"]:
                                x["done"] = True
                                x["done_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        save_tasks(tasks)
                        st.rerun()
                        
                if a2.button("🗑️", help="Delete Task", key=f"x_{t['id']}"):
                    st.session_state.tasks = [x for x in tasks if x["id"] != t["id"]]
                    save_tasks(st.session_state.tasks)
                    st.rerun()
                    
                if api_key and not t["done"]:
                    if a3.button("🤖", help="AI Breakdown", key=f"ai_{t['id']}"):
                        with st.spinner("Analyzing..."):
                            prompt = f"Break down '{t['desc']}' (Priority: {PRI_NAME[t['priority']]}) into 3-5 concrete subtasks. Provide a numbered list under 120 words."
                            system = "You are a productivity assistant. Respond with a numbered subtask list only."
                            result = nvidia_ai_call(api_key, prompt, system)
                            st.info(f"**Subtasks:**\n\n{result}")

# --- TAB 2: Add Task ---
with tab2:
    st.subheader("Add a New Task")
    
    with st.form("add_task_form", clear_on_submit=True):
        desc = st.text_area("Task Description *", height=100)
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority Level", [4, 3, 2, 1], format_func=lambda x: f"{PRI_ICON[x]} {PRI_NAME[x]}", index=2)
        with col2:
            due_date = st.date_input("Due Date", value=None)
            
        submitted = st.form_submit_button("➕ Add Task", use_container_width=True)
        
        if submitted:
            if not desc.strip():
                st.error("Please enter a task description.")
            else:
                new_id = max((t["id"] for t in tasks), default=0) + 1
                new_task = {
                    "id": new_id,
                    "desc": desc.strip(),
                    "priority": int(priority),
                    "done": False,
                    "due": str(due_date) if due_date else None,
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "done_at": None
                }
                tasks.append(new_task)
                save_tasks(tasks)
                st.success(f"✅ Successfully added Task #{new_task['id']}")
                st.rerun()

    st.divider()
    st.subheader("⏱️ AI Time Estimator")
    est_desc = st.text_input("Enter a task description to estimate time requirements:")
    if st.button("Get Estimate"):
        if not api_key:
            st.warning("Please enter your NVIDIA API Key in the sidebar.")
        elif not est_desc.strip():
            st.warning("Please enter a description first.")
        else:
            with st.spinner("Calculating estimate..."):
                prompt = f"Estimate time for: '{est_desc}'. Give: 1) Time, 2) Complexity, 3) One tip. Under 70 words."
                sys_prompt = "You are a realistic project estimator. Be concise."
                result = nvidia_ai_call(api_key, prompt, sys_prompt)
                st.info(result)

# --- TAB 3: AI Coach ---
with tab3:
    st.subheader("🤖 NVIDIA AI Productivity Coach")
    
    if not api_key:
        st.warning("Please enter your NVIDIA API Key in the sidebar to access the AI Coach.")
    else:
        col1, col2 = st.columns(2)
        
        if col1.button("🎯 What should I focus on TODAY?", use_container_width=True):
            pending_tasks = [t for t in tasks if not t["done"]]
            if not pending_tasks:
                st.success("🎉 You have no pending tasks. Great job!")
            else:
                task_list_str = "\n".join(f"- {t['desc']} (Priority: {PRI_NAME[t['priority']]}, Due: {t['due'] or 'None'})" for t in pending_tasks[:15])
                with st.spinner("Reviewing your tasks..."):
                    prompt = f"Pick the top 3 tasks to do TODAY from this list:\n{task_list_str}\nBriefly explain why. Keep it under 100 words."
                    system = "You are a decisive and highly effective productivity coach."
                    response = nvidia_ai_call(api_key, prompt, system)
                    st.success(response)
                    
        if col2.button("📊 Analyze My Productivity", use_container_width=True):
            completion_rate = (done_tasks / total_tasks * 100) if total_tasks else 0
            with st.spinner("Analyzing performance..."):
                prompt = f"Stats: {total_tasks} total tasks, {done_tasks} done ({completion_rate:.0f}%), {overdue_tasks} overdue. Provide 3 insights and 2 actionable tips. Under 100 words."
                system = "You are an honest, data-driven productivity analyst."
                response = nvidia_ai_call(api_key, prompt, system)
                st.info(response)

        st.divider()
        st.write("**Ask your AI Coach a custom question:**")
        user_query = st.text_input("E.g., 'How do I handle my overdue tasks without getting overwhelmed?'")
        
        if st.button("Ask Coach") and user_query:
            pending_str = "; ".join(t["desc"] for t in tasks if not t["done"])[:300]
            with st.spinner("Thinking..."):
                prompt = f"Current Pending Tasks: {pending_str}\nQuestion: {user_query}"
                system = "You are an empathetic, helpful productivity coach. Keep answers under 120 words."
                response = nvidia_ai_call(api_key, prompt, system)
                st.chat_message("assistant").write(response)

# --- TAB 4: Statistics ---
with tab4:
    st.subheader("📊 Task Statistics")
    
    if not tasks:
        st.info("Log some tasks to see your statistics.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Tasks", total_tasks)
        c2.metric("Completed", done_tasks)
        c3.metric("Pending", total_tasks - done_tasks)
        c4.metric("Overdue", overdue_tasks)
        
        st.write("**Overall Progress**")
        progress_val = (done_tasks / total_tasks) if total_tasks > 0 else 0
        st.progress(progress_val, text=f"{progress_val * 100:.0f}% Completed")
        
        st.divider()
        
        st.write("**Priority Distribution**")
        priority_counts = Counter(PRI_NAME[t["priority"]] for t in tasks)
        
        fig = go.Figure(data=[go.Pie(
            labels=list(priority_counts.keys()), 
            values=list(priority_counts.values()),
            hole=0.4, 
            marker_colors=["#22c55e", "#eab308", "#f97316", "#ef4444"]
        )])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
        st.plotly_chart(fig, use_container_width=True)
