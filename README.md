# 📋 SmartTask – Priority-Aware To-Do Manager

> **DecodeLabs Industrial Training · Batch 2026**  
> Author: **Chittem Gowri Sankar** | Viswam Engineering College | CST 2024–28

---

## 🚀 What Makes This Different

SmartTask goes beyond a basic to-do list. It's a **full MVC-architected task engine** with:

- **4-Level Priority System** — URGENT 🔥 / HIGH / MEDIUM / LOW with colour-coded display
- **Due Date Awareness** — Tracks overdue tasks, warns you on launch
- **Tag-Based Filtering** — Organise tasks by project, context, or category
- **Full-Text Search** — Find tasks by keyword or tag instantly
- **Live Dashboard** — Progress bar, tag cloud, overdue alerts
- **Inline Editing** — Update description, priority, tags, or due date
- **ANSI Colour Terminal UI** — Auto-disables in non-TTY environments (CI-safe)
- **JSON Persistence** — Data survives across sessions

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────┐
│                  SmartTask v2.0                  │
├──────────────┬──────────────┬───────────────────┤
│  MODEL       │  VIEW        │  CONTROLLER       │
│  ─────────── │  ─────────── │  ───────────────  │
│  Task        │  display_    │  main()           │
│  dataclass   │  tasks()     │  choice dispatch  │
│              │  display_    │  input helpers    │
│  Priority    │  dashboard() │                   │
│  (IntEnum)   │  ANSI colour │                   │
├──────────────┴──────────────┴───────────────────┤
│  DATA LAYER: JSON (tasks.json)                   │
└─────────────────────────────────────────────────┘
```

---

## ⚙️ Setup & Run

```bash
# No dependencies — pure Python 3.10+
python todo_list.py
```

---

## 💡 Key Python Concepts Used

| Concept | Where Used |
|---|---|
| `@dataclass` | `Task` model with auto `__init__` |
| `IntEnum` | `Priority` – enables comparison & sorting |
| `field(default_factory=...)` | Mutable defaults in dataclass |
| `Optional[str]` | Type-safe nullable fields |
| List comprehensions | All filter/search functions |
| `asdict()` | Dataclass → JSON serialisation |
| `sys.stdout.isatty()` | CI-safe colour detection |
| `date.fromisoformat()` | Due-date arithmetic |
| Decorator pattern | ANSI colour helper lambdas |

---

## 📸 Features Walkthrough

```
╔══════════════════════════════════════════════════════╗
║   ★  SmartTask  ·  DecodeLabs Internship 2026  ★   ║
║      Gowri Chittem  ·  Priority-Aware Task Engine   ║
╚══════════════════════════════════════════════════════╝

  ⚠  2 overdue task(s) need your attention!

  ┌─ TASKS ───────────────────────────────────────┐
  │  [1] Add task          [5] Search tasks        │
  │  [2] View all          [6] Filter by tag       │
  │  [3] Complete task     [7] Edit task           │
  │  [4] Delete task       [8] Dashboard           │
  │                        [0] Exit                │
  └────────────────────────────────────────────────┘

  ✔ [  3] 🔥 URGENT  Submit assignment   #college  DUE TODAY !
  ○ [  4] ◆ HIGH    Fix bug in API      #work     due in 2d
  ○ [  5] ◈ MEDIUM  Read Python docs    #learning  no due date
```

---

## 🧪 Tests

```bash
python -m pytest test_todo.py -v
```

---

## 📁 Files

```
project1_todo_list/
├── todo_list.py   ← Main application
├── test_todo.py   ← Unit tests
├── tasks.json     ← Auto-created on first run
└── README.md      ← This file
```
