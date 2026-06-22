
import json, os, sys
from datetime import datetime, date
from dataclasses import dataclass, asdict, field
from enum import IntEnum
from typing import Optional


_TTY = sys.stdout.isatty()
def _c(text, code): return f"\033[{code}m{text}\033[0m" if _TTY else text

RED    = lambda t: _c(t, "31")
GREEN  = lambda t: _c(t, "32")
YELLOW = lambda t: _c(t, "33")
CYAN   = lambda t: _c(t, "36")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")

class Priority(IntEnum):
    LOW    = 1
    MEDIUM = 2
    HIGH   = 3
    URGENT = 4

_PRI_STYLE = {
    Priority.LOW:    ("◇", "2"),
    Priority.MEDIUM: ("◈", "33"),
    Priority.HIGH:   ("◆", "31"),
    Priority.URGENT: ("🔥", "1;31"),
}

@dataclass
class Task:
    id:           int
    description:  str
    priority:     int           = int(Priority.MEDIUM)
    tags:         list          = field(default_factory=list)
    done:         bool          = False
    due_date:     Optional[str] = None
    created_at:   str           = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    completed_at: Optional[str] = None

    def is_overdue(self) -> bool:
        return (not self.done) and bool(self.due_date) and \
               date.fromisoformat(self.due_date) < date.today()

    def days_until_due(self) -> Optional[int]:
        if not self.due_date:
            return None
        return (date.fromisoformat(self.due_date) - date.today()).days

DATA_FILE = "tasks.json"

def load_tasks() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return [Task(**r) for r in json.load(f)]

def save_tasks(tasks: list) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump([asdict(t) for t in tasks], f, indent=2)

def _next_id(tasks: list) -> int:
    return max((t.id for t in tasks), default=0) + 1


def add_task(tasks, description, priority=Priority.MEDIUM, tags=None, due_date=None):
    task = Task(
        id=_next_id(tasks), description=description.strip(),
        priority=int(priority),
        tags=[t.lower().strip() for t in (tags or [])],
        due_date=due_date,
    )
    tasks.append(task)
    return task

def complete_task(tasks, task_id):
    for t in tasks:
        if t.id == task_id and not t.done:
            t.done = True
            t.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            return True
    return False

def delete_task(tasks, task_id):
    for i, t in enumerate(tasks):
        if t.id == task_id:
            tasks.pop(i); return True
    return False

def edit_task(tasks, task_id, **kwargs):
    for t in tasks:
        if t.id == task_id:
            for k, v in kwargs.items():
                if hasattr(t, k): setattr(t, k, v)
            return True
    return False

def search_tasks(tasks, query):
    q = query.lower()
    return [t for t in tasks if q in t.description.lower() or q in " ".join(t.tags)]

def filter_by_tag(tasks, tag):
    return [t for t in tasks if tag.lower() in t.tags]

def get_pending(tasks):
    return sorted([t for t in tasks if not t.done],
                  key=lambda t: (-t.priority, t.due_date or "9999-99-99"))

def get_overdue(tasks):
    return [t for t in tasks if t.is_overdue()]

BANNER = """
╔══════════════════════════════════════════════════════╗
║   ★  SmartTask  ·  DecodeLabs Internship 2026  ★   ║
║      Gowri Chittem  ·  Priority-Aware Task Engine   ║
╚══════════════════════════════════════════════════════╝"""

MENU = """
  ┌─ TASKS ───────────────────────────────────────┐
  │  [1] Add task          [5] Search tasks        │
  │  [2] View all          [6] Filter by tag       │
  │  [3] Complete task     [7] Edit task           │
  │  [4] Delete task       [8] Dashboard           │
  │                        [0] Exit                │
  └────────────────────────────────────────────────┘"""


def _pri_label(p):
    icon, code = _PRI_STYLE[Priority(p)]
    return _c(f"{icon} {Priority(p).name:<6}", code)

def _due_label(task):
    if not task.due_date:  return DIM("no due date")
    days = task.days_until_due()
    if task.is_overdue():   return RED(f"OVERDUE {-days}d")
    if days == 0:           return YELLOW("DUE TODAY !")
    if days <= 3:           return YELLOW(f"due in {days}d")
    return DIM(f"due {task.due_date}")

def display_tasks(tasks, title="All Tasks"):
    print(f"\n  {BOLD('──')} {CYAN(title)} {BOLD('──')}")
    if not tasks:
        print(DIM("  (nothing here)")); return
    for t in tasks:
        status   = GREEN("✔") if t.done else "○"
        tags_str = (" " + "  ".join(CYAN(f"#{g}") for g in t.tags)) if t.tags else ""
        desc     = DIM(t.description) if t.done else t.description
        print(f"  {status} [{t.id:>3}] {_pri_label(t.priority)}  {desc}{tags_str}   {_due_label(t)}")

def display_dashboard(tasks):
    total   = len(tasks)
    done    = sum(1 for t in tasks if t.done)
    pending = total - done
    overdue = len(get_overdue(tasks))
    urgent  = sum(1 for t in tasks if not t.done and t.priority == Priority.URGENT)
    pct     = (done / total * 100) if total else 0
    bar     = GREEN("█") * int(pct / 4) + DIM("░") * (25 - int(pct / 4))

    all_tags: dict = {}
    for t in tasks:
        for tag in t.tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1
    tag_cloud = "  ".join(f"{CYAN('#'+k)}({v})" for k, v in
                          sorted(all_tags.items(), key=lambda x: -x[1])[:8])

    print(f"""
  ╔══════════════════════════════════════════╗
  ║  {BOLD('SMARTTASK  DASHBOARD')}                  ║
  ╠══════════════════════════════════════════╣
  ║  Total    : {BOLD(str(total)):<6}  Done    : {GREEN(str(done)):<6}  ║
  ║  Pending  : {YELLOW(str(pending)):<6}  Urgent  : {RED(str(urgent)):<6}  ║
  ║  Overdue  : {RED(str(overdue)):<6}                     ║
  ║                                          ║
  ║  Progress  [{bar}] {pct:.0f}%  ║
  ╚══════════════════════════════════════════╝

  Tag cloud: {tag_cloud or DIM('(no tags yet)')}
""")



def _input_priority():
    print("\n  Priority:")
    for p in Priority:
        icon, code = _PRI_STYLE[p]
        print(f"    [{p.value}] {_c(icon + ' ' + p.name, code)}")
    while True:
        raw = input("  Choose [1-4] (default=2): ").strip() or "2"
        if raw in "1234": return Priority(int(raw))
        print(RED("  ✗ Enter 1, 2, 3, or 4."))

def _input_due():
    raw = input("  Due date [YYYY-MM-DD] or blank: ").strip()
    if not raw: return None
    try:
        date.fromisoformat(raw); return raw
    except ValueError:
        print(YELLOW("  ⚠ Invalid date – skipped.")); return None

def _input_tags():
    raw = input("  Tags (comma-separated, e.g. work,urgent): ").strip()
    return [t.strip() for t in raw.split(",") if t.strip()] if raw else []


def main():
    print(CYAN(BANNER))
    tasks = load_tasks()

    overdue = get_overdue(tasks)
    if overdue:
        print(RED(f"\n  ⚠  {len(overdue)} overdue task(s) need your attention!\n"))
    print(GREEN(f"  ✓ Loaded {len(tasks)} task(s)."))

    while True:
        print(MENU)
        choice = input("\n  Enter choice: ").strip()

        if choice == "1":
            desc = input("  Task description: ").strip()
            if not desc: print(RED("  ✗ Description cannot be empty.")); continue
            pri  = _input_priority()
            tags = _input_tags()
            due  = _input_due()
            t    = add_task(tasks, desc, pri, tags, due)
            save_tasks(tasks)
            print(GREEN(f"  ✓ Added [{t.id}]: \"{t.description}\"  {_pri_label(t.priority)}"))

        elif choice == "2":
            display_tasks(tasks)

        elif choice == "3":
            display_tasks(get_pending(tasks), "Pending Tasks")
            try:
                tid = int(input("\n  Task ID to complete: "))
                if complete_task(tasks, tid):
                    save_tasks(tasks)
                    print(GREEN(f"  ✓ Task {tid} completed! 🎉"))
                else:
                    print(RED(f"  ✗ Task {tid} not found or already done."))
            except ValueError:
                print(RED("  ✗ Enter a valid integer."))

        elif choice == "4":
            display_tasks(tasks)
            try:
                tid = int(input("\n  Task ID to delete: "))
                if input(f"  Confirm delete task {tid}? [y/N]: ").strip().lower() == "y":
                    if delete_task(tasks, tid):
                        save_tasks(tasks); print(GREEN(f"  ✓ Task {tid} deleted."))
                    else:
                        print(RED(f"  ✗ Task {tid} not found."))
            except ValueError:
                print(RED("  ✗ Enter a valid integer."))

        elif choice == "5":
            q = input("  Search query: ").strip()
            results = search_tasks(tasks, q)
            display_tasks(results, f"Results for \"{q}\"")
            print(f"  {len(results)} match(es).")

        elif choice == "6":
            tag = input("  Tag (without #): ").strip().lstrip("#")
            display_tasks(filter_by_tag(tasks, tag), f"Tag: #{tag}")

        elif choice == "7":
            display_tasks(tasks)
            try:
                tid = int(input("\n  Task ID to edit: "))
                if not any(t.id == tid for t in tasks):
                    print(RED(f"  ✗ Task {tid} not found.")); continue
                desc = input("  New description (blank = keep): ").strip()
                pri  = _input_priority()
                due  = _input_due()
                tags = _input_tags()
                updates = {"priority": int(pri)}
                if desc: updates["description"] = desc
                if due:  updates["due_date"] = due
                if tags: updates["tags"] = [t.lower() for t in tags]
                edit_task(tasks, tid, **updates)
                save_tasks(tasks)
                print(GREEN(f"  ✓ Task {tid} updated."))
            except ValueError:
                print(RED("  ✗ Enter a valid integer."))

        elif choice == "8":
            display_dashboard(tasks)

        elif choice == "0":
            save_tasks(tasks)
            print(GREEN("\n  All tasks saved. See you! 👋\n")); break

        else:
            print(RED("  ✗ Invalid option."))

if __name__ == "__main__":
    main()
