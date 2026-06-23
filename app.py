"""
SmartTask AI — DecodeLabs Internship 2026
Chittem Gowri Sankar | Viswam Engineering College, JNTUA
"""
import streamlit as st
import plotly.graph_objects as go
import json, os, requests
from datetime import datetime, date
from collections import Counter

# ── MUST be first streamlit call ─────────────────────────────
st.set_page_config(page_title="SmartTask AI", page_icon="🧠", layout="wide")

# ── Paths: use relative dir so it works on Streamlit Cloud ───
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_FILE  = os.path.join(BASE_DIR, "tasks.json")

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0a0e1a;color:#e2e8f0;}
.hdr{background:linear-gradient(135deg,#1a1f35,#0f172a);border:1px solid #2d3748;
     border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.2rem;position:relative;overflow:hidden;}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
              background:linear-gradient(90deg,#6366f1,#8b5cf6,#ec4899);}
.hdr h1{font-size:1.8rem;font-weight:700;color:#f1f5f9;margin:0;}
.hdr p{color:#94a3b8;margin:0.2rem 0 0;font-size:0.85rem;}
.card{background:#111827;border:1px solid #1f2937;border-radius:10px;
      padding:0.9rem 1.1rem;margin-bottom:0.6rem;}
.card.pl{border-left:3px solid #ef4444;}
.card.ph{border-left:3px solid #f97316;}
.card.pm{border-left:3px solid #eab308;}
.card.pw{border-left:3px solid #22c55e;}
.card.done{opacity:0.45;}
.ai-box{background:linear-gradient(135deg,#0f172a,#1e1b4b);border:1px solid #3730a3;
         border-radius:10px;padding:1rem 1.25rem;margin-top:0.8rem;}
.ai-label{font-size:0.65rem;text-transform:uppercase;letter-spacing:.1em;
           color:#818cf8;margin-bottom:.4rem;font-weight:600;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{
  background:#111827!important;border:1px solid #374151!important;
  color:#e2e8f0!important;border-radius:7px!important;}
.stSelectbox>div>div{background:#111827!important;border:1px solid #374151!important;
  color:#e2e8f0!important;border-radius:7px!important;}
</style>
""", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────
PRI_ICON  = {1:"🟢",2:"🟡",3:"🟠",4:"🔴"}
PRI_NAME  = {1:"Low",2:"Medium",3:"High",4:"Urgent"}
PRI_CSS   = {1:"pw",2:"pm",3:"ph",4:"pl"}

def load():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except Exception: return []

def save(tasks):
    with open(DATA_FILE,"w") as f: json.dump(tasks, f, indent=2)

def is_overdue(t):
    return not t["done"] and bool(t["due"]) and date.fromisoformat(t["due"]) < date.today()

def days_left(t):
    if not t["due"]: return None
    return (date.fromisoformat(t["due"]) - date.today()).days

# ── NVIDIA API ────────────────────────────────────────────────
def nvidia(api_key, prompt, system="You are a helpful assistant. Be concise.", max_tokens=400):
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            json={"model":"meta/llama-3.1-8b-instruct",
                  "messages":[{"role":"system","content":system},
                               {"role":"user","content":prompt}],
                  "temperature":0.6,"max_tokens":max_tokens},
            timeout=25
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Try again."
    except Exception as e:
        return f"⚠️ API error: {e}"

# ── Session state ─────────────────────────────────────────────
if "tasks" not in st.session_state:
    st.session_state.tasks = load()

tasks = st.session_state.tasks

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>🧠 SmartTask AI</h1>
  <p>DecodeLabs Internship 2026 · Chittem Gowri Sankar · NVIDIA NIM</p>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    api_key = st.text_input("🔑 NVIDIA API Key", type="password", placeholder="nvapi-...")
    st.caption("[Get key →](https://build.nvidia.com)")
    st.divider()
    total   = len(tasks)
    done    = sum(1 for t in tasks if t["done"])
    overdue = sum(1 for t in tasks if is_overdue(t))
    st.metric("Total", total); st.metric("Done", done); st.metric("Overdue", overdue)
    if total: st.progress(done/total, text=f"{done/total:.0%} complete")
    st.divider()
    view = st.radio("View", ["All","Pending","Overdue","Done"])

# ── Tabs ──────────────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs(["📋 Tasks","➕ Add","🤖 AI Coach","📊 Stats"])

# ── TAB 1: Tasks ──────────────────────────────────────────────
with t1:
    pool = tasks
    if view == "Pending": pool = [t for t in tasks if not t["done"]]
    elif view == "Overdue": pool = [t for t in tasks if is_overdue(t)]
    elif view == "Done": pool = [t for t in tasks if t["done"]]
    pool = sorted(pool, key=lambda t:(-t["priority"], t["due"] or "9999"))

    q = st.text_input("🔍 Search", placeholder="keyword…")
    if q: pool = [t for t in pool if q.lower() in t["desc"].lower()]

    if not pool:
        st.info(f"No tasks in '{view}' view.")

    for t in pool:
        d = days_left(t)
        if t["due"]:
            if is_overdue(t):   badge=f'<span style="color:#ef4444;font-weight:700">⚠ OVERDUE {-d}d</span>'
            elif d == 0:         badge='<span style="color:#f59e0b;font-weight:700">🔔 TODAY</span>'
            elif d and d <= 3:   badge=f'<span style="color:#fbbf24">⏳ {d}d</span>'
            else:                badge=f'<span style="color:#4b5563;font-size:.8rem">📅 {t["due"]}</span>'
        else: badge=""
        css = PRI_CSS[t["priority"]]
        st.markdown(f"""
        <div class="card {css} {'done' if t['done'] else ''}">
          <div style="display:flex;justify-content:space-between">
            <span>{'✅' if t['done'] else '⬜'} <strong style="color:{'#6b7280' if t['done'] else '#f1f5f9'}">[#{t['id']}] {t['desc']}</strong>
              <span style="margin-left:8px;font-size:.75rem;color:#6b7280">{PRI_ICON[t['priority']]} {PRI_NAME[t['priority']]}</span></span>
            <span>{badge}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1,1,5])
        if not t["done"] and c1.button("✅", key=f"d{t['id']}"):
            for x in tasks:
                if x["id"]==t["id"]: x["done"]=True; x["done_at"]=datetime.now().strftime("%Y-%m-%d %H:%M")
            save(tasks); st.rerun()
        if c2.button("🗑", key=f"x{t['id']}"):
            st.session_state.tasks=[x for x in tasks if x["id"]!=t["id"]]
            save(st.session_state.tasks); st.rerun()
        if api_key and not t["done"] and c3.button("🤖 Break down", key=f"ai{t['id']}"):
            with st.spinner("Analyzing…"):
                result = nvidia(api_key,
                    f"Break '{t['desc']}' (priority:{PRI_NAME[t['priority']]}) into 3-5 concrete subtasks. Numbered list. Under 120 words.",
                    "You are a productivity assistant. Respond with a numbered subtask list only.")
            st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 NVIDIA · Subtask Breakdown</div>'
                        f'<div style="color:#c7d2fe;white-space:pre-wrap">{result}</div></div>', unsafe_allow_html=True)

# ── TAB 2: Add ────────────────────────────────────────────────
with t2:
    st.subheader("Add Task")
    desc     = st.text_area("Description *", height=80)
    c1, c2   = st.columns(2)
    priority = c1.selectbox("Priority", [4,3,2,1], format_func=lambda x:f"{PRI_ICON[x]} {PRI_NAME[x]}", index=2)
    due      = c2.date_input("Due date", value=None)

    col_a, col_b = st.columns(2)
    if col_a.button("➕ Add Task", type="primary", use_container_width=True):
        if not desc.strip(): st.error("Description required.")
        else:
            new = {"id": max((t["id"] for t in tasks), default=0)+1,
                   "desc": desc.strip(), "priority": int(priority),
                   "done": False, "due": str(due) if due else None,
                   "created": datetime.now().strftime("%Y-%m-%d %H:%M"), "done_at": None}
            tasks.append(new); save(tasks)
            st.success(f"✅ Added #{new['id']}: {new['desc']}"); st.rerun()
    if api_key and col_b.button("⏱ Estimate Time", use_container_width=True):
        if not desc.strip(): st.warning("Enter description first.")
        else:
            with st.spinner():
                r = nvidia(api_key, f"Estimate time for: '{desc}'. Give: 1)Time 2)Complexity 3)One tip. Under 70 words.",
                           "You are a project estimator. Be concise.")
            st.info(r)

# ── TAB 3: AI Coach ───────────────────────────────────────────
with t3:
    st.subheader("🤖 NVIDIA AI Productivity Coach")
    if not api_key:
        st.warning("Enter NVIDIA API key in sidebar.")
    else:
        c1, c2 = st.columns(2)
        if c1.button("🎯 What to do TODAY?", type="primary", use_container_width=True):
            pending = [t for t in tasks if not t["done"]]
            if not pending: st.success("🎉 All done!")
            else:
                tlist = "\n".join(f"- {t['desc']} (P:{PRI_NAME[t['priority']]}, due:{t['due'] or 'none'})" for t in pending[:15])
                with st.spinner():
                    r = nvidia(api_key, f"Pick top 3 tasks to do TODAY:\n{tlist}\nExplain briefly. Under 100 words.",
                               "You are a decisive productivity coach.")
                st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 Today\'s Priority</div>'
                            f'<div style="color:#c7d2fe;white-space:pre-wrap">{r}</div></div>', unsafe_allow_html=True)
        if c2.button("📊 Productivity Analysis", use_container_width=True):
            rate = done/total*100 if total else 0
            with st.spinner():
                r = nvidia(api_key, f"Stats: {total} tasks, {done} done ({rate:.0f}%), {overdue} overdue. 3 insights + 2 tips. Under 100 words.",
                           "You are a productivity analyst. Be honest.")
            st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 Analysis</div>'
                        f'<div style="color:#c7d2fe;white-space:pre-wrap">{r}</div></div>', unsafe_allow_html=True)
        st.divider()
        q = st.text_input("Ask anything about your tasks")
        if st.button("Ask →") and q:
            pending_str = "; ".join(t["desc"] for t in tasks if not t["done"])[:300]
            with st.spinner():
                r = nvidia(api_key, f"Tasks: {pending_str}\nQuestion: {q}", "You are a helpful productivity coach. Under 120 words.")
            st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 Answer</div>'
                        f'<div style="color:#c7d2fe;white-space:pre-wrap">{r}</div></div>', unsafe_allow_html=True)

# ── TAB 4: Stats ──────────────────────────────────────────────
with t4:
    if not tasks:
        st.info("Add tasks to see stats.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", total); col2.metric("Done", done)
        col3.metric("Pending", total-done); col4.metric("Overdue", overdue)
        st.progress(done/total if total else 0, text=f"{done/total*100:.0f}% complete")

        pri_counts = Counter(PRI_NAME[t["priority"]] for t in tasks)
        fig = go.Figure(go.Pie(
            labels=list(pri_counts.keys()), values=list(pri_counts.values()),
            hole=0.55, marker_colors=["#22c55e","#eab308","#f97316","#ef4444"]))
        fig.update_layout(title="Priority Distribution", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                          height=280, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
