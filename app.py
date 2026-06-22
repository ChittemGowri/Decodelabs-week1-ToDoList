"""
SmartTask AI — DecodeLabs Internship 2026
Chittem Gowri Sankar | Viswam Engineering College, JNTUA
NVIDIA NIM-powered intelligent task management
"""

import streamlit as st
import json, os
from datetime import datetime, date
from dataclasses import dataclass, asdict, field
from enum import IntEnum
from typing import Optional
import requests

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="SmartTask AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0a0e1a; color: #e2e8f0; }

.main-header {
    background: linear-gradient(135deg, #1a1f35 0%, #0f172a 100%);
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
}
.main-header h1 { font-size: 2rem; font-weight: 700; color: #f1f5f9; margin: 0; }
.main-header p  { color: #94a3b8; margin: 0.25rem 0 0; font-size: 0.9rem; }

.task-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.task-card:hover { border-color: #374151; }
.task-card.done  { opacity: 0.5; }

.priority-urgent { border-left: 3px solid #ef4444; }
.priority-high   { border-left: 3px solid #f97316; }
.priority-medium { border-left: 3px solid #eab308; }
.priority-low    { border-left: 3px solid #22c55e; }

.tag {
    display: inline-block;
    background: #1e293b;
    color: #7c3aed;
    border: 1px solid #312e81;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    margin-right: 4px;
    font-family: 'JetBrains Mono', monospace;
}

.stat-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
}
.stat-value { font-size: 2rem; font-weight: 700; color: #f1f5f9; }
.stat-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }

.ai-response {
    background: linear-gradient(135deg, #0f172a, #1e1b4b);
    border: 1px solid #3730a3;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
}
.ai-response .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #818cf8;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

.overdue-badge { color: #ef4444; font-weight: 600; font-size: 0.8rem; }
.due-today     { color: #f59e0b; font-weight: 600; font-size: 0.8rem; }
.due-soon      { color: #fbbf24; font-size: 0.8rem; }

.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #111827 !important;
    border: 1px solid #374151 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid #374151 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
div[data-testid="stMetricValue"] { color: #f1f5f9 !important; }
.stProgress > div > div { background: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data model ────────────────────────────────────────────────
class Priority(IntEnum):
    LOW = 1; MEDIUM = 2; HIGH = 3; URGENT = 4

PRI_ICON  = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}
PRI_NAME  = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
PRI_CLASS = {1: "priority-low", 2: "priority-medium", 3: "priority-high", 4: "priority-urgent"}

DATA_FILE = "/tmp/smarttask_tasks.json"

def load_tasks():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)

def save_tasks(tasks):
    with open(DATA_FILE, "w") as f: json.dump(tasks, f, indent=2)

def next_id(tasks): return max((t["id"] for t in tasks), default=0) + 1

def is_overdue(t):
    return (not t["done"]) and bool(t["due_date"]) and \
           date.fromisoformat(t["due_date"]) < date.today()

def days_until(t):
    if not t["due_date"]: return None
    return (date.fromisoformat(t["due_date"]) - date.today()).days

# ── NVIDIA API ────────────────────────────────────────────────
def call_nvidia(api_key: str, messages: list, system: str = "") -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": msgs,
        "temperature": 0.6,
        "max_tokens": 600,
    }
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ NVIDIA API error: {e}"

def ai_breakdown(api_key: str, task: str, priority: str) -> str:
    return call_nvidia(api_key, [{"role": "user",
        "content": f"Break this task into 3-5 concrete, actionable subtasks. Task: '{task}' (Priority: {priority}). Format as numbered list. Be specific and practical. Keep it under 150 words."}],
        system="You are a productivity assistant. Respond concisely with a numbered subtask list only.")

def ai_prioritize(api_key: str, tasks: list) -> str:
    if not tasks: return "No tasks to analyze."
    task_list = "\n".join([f"- {t['description']} (Priority: {PRI_NAME[t['priority']]}, Due: {t['due_date'] or 'No date'})" 
                           for t in tasks if not t["done"]])
    return call_nvidia(api_key, [{"role": "user",
        "content": f"Analyze these tasks and tell me which 3 I should do TODAY and why, considering priorities and deadlines:\n{task_list}\nKeep your response under 120 words."}],
        system="You are a productivity coach. Be direct and decisive.")

def ai_task_estimate(api_key: str, task: str) -> str:
    return call_nvidia(api_key, [{"role": "user",
        "content": f"Estimate time required for: '{task}'. Give: 1) Estimated time 2) Complexity (Low/Medium/High) 3) One pro tip. Under 80 words."}],
        system="You are an expert project estimator. Be concise and practical.")

# ── Session state ─────────────────────────────────────────────
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()
if "ai_output" not in st.session_state:
    st.session_state.ai_output = ""
if "ai_label" not in st.session_state:
    st.session_state.ai_label = ""

tasks = st.session_state.tasks

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧠 SmartTask AI</h1>
    <p>DecodeLabs Internship 2026 · Chittem Gowri Sankar · NVIDIA NIM Powered</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("NVIDIA API Key", type="password", placeholder="nvapi-...")
    st.caption("Get your key at [build.nvidia.com](https://build.nvidia.com)")
    
    st.divider()
    st.markdown("### 📊 Quick Stats")
    total   = len(tasks)
    done    = sum(1 for t in tasks if t["done"])
    pending = total - done
    overdue = sum(1 for t in tasks if is_overdue(t))
    urgent  = sum(1 for t in tasks if not t["done"] and t["priority"] == 4)
    
    col1, col2 = st.columns(2)
    col1.metric("Total", total)
    col2.metric("Done", done, f"+{done}" if done else None)
    col1.metric("Pending", pending)
    col2.metric("Overdue", overdue, delta_color="inverse")
    
    if total > 0:
        pct = done / total
        st.progress(pct, text=f"Progress: {pct:.0%}")
    
    st.divider()
    view = st.radio("📋 View", ["All Tasks", "Pending", "Overdue", "Completed"], index=0)

# ── Main tabs ─────────────────────────────────────────────────
tab_list, tab_add, tab_ai, tab_dash = st.tabs(["📋 Tasks", "➕ Add Task", "🤖 AI Assistant", "📊 Dashboard"])

# ────────────── TAB 1: TASK LIST ──────────────────────────────
with tab_list:
    # Filter
    if view == "All Tasks":    show = tasks
    elif view == "Pending":    show = [t for t in tasks if not t["done"]]
    elif view == "Overdue":    show = [t for t in tasks if is_overdue(t)]
    else:                      show = [t for t in tasks if t["done"]]
    
    # Sort pending by priority
    show_sorted = sorted(show, key=lambda t: (-t["priority"], t["due_date"] or "9999"))
    
    if not show_sorted:
        st.info(f"No tasks in '{view}' view.")
    
    search = st.text_input("🔍 Search tasks", placeholder="Search description or tag…")
    if search:
        q = search.lower()
        show_sorted = [t for t in show_sorted if q in t["description"].lower() or q in " ".join(t.get("tags", []))]
    
    for t in show_sorted:
        days = days_until(t)
        due_html = ""
        if t["due_date"]:
            if is_overdue(t):
                due_html = f'<span class="overdue-badge">⚠ OVERDUE {-days}d</span>'
            elif days == 0:
                due_html = '<span class="due-today">🔔 DUE TODAY</span>'
            elif days and days <= 3:
                due_html = f'<span class="due-soon">⏳ {days}d left</span>'
            else:
                due_html = f'<span style="color:#4b5563;font-size:0.8rem">📅 {t["due_date"]}</span>'
        
        tags_html = " ".join(f'<span class="tag">#{g}</span>' for g in t.get("tags", []))
        done_style = "task-card done" if t["done"] else "task-card"
        pri_class  = PRI_CLASS[t["priority"]]
        check = "✅" if t["done"] else "⬜"
        
        st.markdown(f"""
        <div class="{done_style} {pri_class}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                    <span style="margin-right:8px">{check}</span>
                    <strong style="color:{'#6b7280' if t['done'] else '#f1f5f9'}">[#{t['id']}] {t['description']}</strong>
                    <span style="margin-left:8px;font-size:0.75rem;color:#6b7280">{PRI_ICON[t['priority']]} {PRI_NAME[t['priority']]}</span>
                </div>
                <div>{due_html}</div>
            </div>
            <div style="margin-top:6px">{tags_html}</div>
            <div style="font-size:0.7rem;color:#4b5563;margin-top:4px">Created: {t.get('created_at','')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 4])
        if not t["done"]:
            if c1.button("✅ Done", key=f"done_{t['id']}"):
                for x in tasks:
                    if x["id"] == t["id"]:
                        x["done"] = True
                        x["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_tasks(tasks)
                st.rerun()
        if c2.button("🗑 Del", key=f"del_{t['id']}"):
            st.session_state.tasks = [x for x in tasks if x["id"] != t["id"]]
            save_tasks(st.session_state.tasks)
            st.rerun()
        
        # AI breakdown per task
        if api_key and not t["done"]:
            if c3.button("🤖 AI Breakdown", key=f"ai_{t['id']}"):
                with st.spinner("Analyzing task…"):
                    result = ai_breakdown(api_key, t["description"], PRI_NAME[t["priority"]])
                    st.session_state.ai_output = result
                    st.session_state.ai_label  = f"AI Breakdown: {t['description'][:40]}…"
        
        if st.session_state.ai_output and st.session_state.ai_label and f"AI Breakdown: {t['description'][:40]}" in st.session_state.ai_label:
            st.markdown(f"""
            <div class="ai-response">
                <div class="label">🤖 NVIDIA AI · {st.session_state.ai_label}</div>
                <div style="color:#c7d2fe;white-space:pre-wrap">{st.session_state.ai_output}</div>
            </div>
            """, unsafe_allow_html=True)

# ────────────── TAB 2: ADD TASK ───────────────────────────────
with tab_add:
    st.subheader("Create New Task")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        desc = st.text_area("📝 Task description *", placeholder="What needs to be done?", height=100)
    with col2:
        priority = st.selectbox("🎯 Priority", [4, 3, 2, 1], 
                                format_func=lambda x: f"{PRI_ICON[x]} {PRI_NAME[x]}", index=2)
        due_date = st.date_input("📅 Due date (optional)", value=None)
    
    tags_raw = st.text_input("🏷 Tags", placeholder="work, urgent, study (comma-separated)")
    
    c1, c2 = st.columns([1, 1])
    
    if c1.button("➕ Add Task", type="primary", use_container_width=True):
        if not desc.strip():
            st.error("Description cannot be empty.")
        else:
            tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
            new_task = {
                "id": next_id(tasks),
                "description": desc.strip(),
                "priority": int(priority),
                "tags": tags,
                "done": False,
                "due_date": str(due_date) if due_date else None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "completed_at": None,
            }
            tasks.append(new_task)
            save_tasks(tasks)
            st.success(f"✅ Task #{new_task['id']} added: {new_task['description']}")
            st.rerun()
    
    if api_key and c2.button("⏱ AI Time Estimate", use_container_width=True):
        if not desc.strip():
            st.warning("Enter a description first.")
        else:
            with st.spinner("Estimating…"):
                result = ai_task_estimate(api_key, desc)
                st.markdown(f"""
                <div class="ai-response">
                    <div class="label">🤖 NVIDIA AI · Time & Complexity Estimate</div>
                    <div style="color:#c7d2fe">{result}</div>
                </div>
                """, unsafe_allow_html=True)

# ────────────── TAB 3: AI ASSISTANT ──────────────────────────
with tab_ai:
    st.subheader("🤖 NVIDIA AI Productivity Coach")
    
    if not api_key:
        st.warning("🔑 Enter your NVIDIA API key in the sidebar to enable AI features.")
    else:
        st.info("Powered by Meta Llama 3.1 via NVIDIA NIM API")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 What should I do TODAY?", use_container_width=True, type="primary"):
                pending_tasks = [t for t in tasks if not t["done"]]
                if not pending_tasks:
                    st.info("No pending tasks! You're all caught up. 🎉")
                else:
                    with st.spinner("AI is analyzing your workload…"):
                        result = ai_prioritize(api_key, pending_tasks)
                        st.markdown(f"""
                        <div class="ai-response">
                            <div class="label">🤖 NVIDIA AI · Daily Priority Recommendation</div>
                            <div style="color:#c7d2fe;white-space:pre-wrap">{result}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📊 Productivity Analysis", use_container_width=True):
                with st.spinner("Analyzing patterns…"):
                    completed = [t for t in tasks if t["done"]]
                    total_t   = len(tasks)
                    done_t    = len(completed)
                    rate      = done_t / total_t * 100 if total_t else 0
                    overdue_c = sum(1 for t in tasks if is_overdue(t))
                    analysis  = call_nvidia(api_key, [{"role": "user",
                        "content": f"My task stats: {total_t} total, {done_t} completed ({rate:.0f}%), {overdue_c} overdue. Give me 3 insights about my productivity and 2 improvement tips. Under 120 words."}],
                        system="You are a productivity analyst. Be honest and direct.")
                    st.markdown(f"""
                    <div class="ai-response">
                        <div class="label">🤖 NVIDIA AI · Productivity Analysis</div>
                        <div style="color:#c7d2fe;white-space:pre-wrap">{analysis}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("#### 💬 Ask the AI Anything")
        user_q = st.text_input("Your question", placeholder="How do I manage procrastination?")
        if st.button("Ask AI →") and user_q:
            with st.spinner("Thinking…"):
                pending_list = "\n".join([f"- {t['description']}" for t in tasks if not t["done"]][:10])
                ctx = f"User has these pending tasks:\n{pending_list}\n\nQuestion: {user_q}"
                result = call_nvidia(api_key, [{"role": "user", "content": ctx}],
                    system="You are a productivity and task management coach. Be helpful, direct, and concise. Max 150 words.")
                st.markdown(f"""
                <div class="ai-response">
                    <div class="label">🤖 NVIDIA AI Response</div>
                    <div style="color:#c7d2fe;white-space:pre-wrap">{result}</div>
                </div>
                """, unsafe_allow_html=True)

# ────────────── TAB 4: DASHBOARD ─────────────────────────────
with tab_dash:
    st.subheader("📊 Analytics Dashboard")
    
    if not tasks:
        st.info("Add tasks to see your analytics.")
    else:
        import plotly.graph_objects as go
        import plotly.express as px
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tasks", total)
        col2.metric("Completed",   done,    f"{done/total*100:.0f}%" if total else "0%")
        col3.metric("Overdue",     overdue, delta_color="inverse")
        col4.metric("Urgent",      urgent,  delta_color="inverse")
        
        # Priority distribution
        from collections import Counter
        pri_counts = Counter(PRI_NAME[t["priority"]] for t in tasks)
        
        fig1 = go.Figure(go.Pie(
            labels=list(pri_counts.keys()),
            values=list(pri_counts.values()),
            hole=0.6,
            marker_colors=["#22c55e", "#eab308", "#f97316", "#ef4444"]
        ))
        fig1.update_layout(
            title="Priority Distribution",
            paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a",
            font_color="#e2e8f0", showlegend=True,
            height=300, margin=dict(t=50, b=20, l=0, r=0)
        )
        
        # Completion over time
        completed_tasks = [t for t in tasks if t.get("completed_at")]
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_b:
            # Tag cloud
            all_tags = []
            for t in tasks:
                all_tags.extend(t.get("tags", []))
            tag_counts = Counter(all_tags)
            if tag_counts:
                tags_df = {"Tag": list(tag_counts.keys()), "Count": list(tag_counts.values())}
                fig2 = go.Figure(go.Bar(
                    x=list(tag_counts.keys()),
                    y=list(tag_counts.values()),
                    marker_color="#6366f1"
                ))
                fig2.update_layout(
                    title="Most Used Tags",
                    paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
                    font_color="#e2e8f0", height=300,
                    xaxis=dict(color="#6b7280"), yaxis=dict(color="#6b7280"),
                    margin=dict(t=50, b=20, l=0, r=0)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Add tags to see the tag cloud.")
        
        # Progress bar
        st.markdown(f"#### Overall Progress: {done}/{total} tasks complete")
        st.progress(done / total if total else 0)
