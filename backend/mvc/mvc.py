"""
MVC PATTERN (Model-View-Controller)
====================================
Category : Backend / Architectural
Interview tag: "Separate an application into three interconnected
                components: Model (data/business logic), View
                (presentation), and Controller (input handling/coordination)."

Real-world backend use case in this file
-----------------------------------------
A minimal Task Manager (like a tiny Trello). We simulate a request/response
cycle without a real web framework so the pattern is visible end-to-end:

    Controller receives "input" (like an HTTP request)
        -> calls Model to read/mutate data
        -> selects a View to render the result
        -> returns the rendered output (like an HTTP response)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import itertools


# ---------------------------------------------------------------------------
# MODEL — owns data and business/domain rules. Knows NOTHING about HTTP,
# JSON, HTML, or how it will be displayed.
# ---------------------------------------------------------------------------
@dataclass
class Task:
    id: int
    title: str
    done: bool = False


class TaskModel:
    """The Model: data + business rules. No knowledge of views/controllers."""

    def __init__(self):
        self._tasks: dict[int, Task] = {}
        self._id_counter = itertools.count(1)

    def create_task(self, title: str) -> Task:
        if not title.strip():
            raise ValueError("Task title cannot be empty")
        task = Task(id=next(self._id_counter), title=title.strip())
        self._tasks[task.id] = task
        return task

    def complete_task(self, task_id: int) -> Task:
        task = self._get_or_raise(task_id)
        task.done = True
        return task

    def list_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def _get_or_raise(self, task_id: int) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        return task


# ---------------------------------------------------------------------------
# VIEW — purely responsible for presentation/formatting. Same Model data
# can be rendered by multiple views (JSON API vs. plain-text CLI, etc.)
# ---------------------------------------------------------------------------
class JsonTaskView:
    """Renders tasks the way a REST API response would look."""

    def render_list(self, tasks: list[Task]) -> dict:
        return {
            "tasks": [
                {"id": t.id, "title": t.title, "done": t.done} for t in tasks
            ]
        }

    def render_single(self, task: Task) -> dict:
        return {"id": task.id, "title": task.title, "done": task.done}

    def render_error(self, message: str) -> dict:
        return {"error": message}


class PlainTextTaskView:
    """Renders tasks as human-readable text — e.g. for a CLI tool."""

    def render_list(self, tasks: list[Task]) -> str:
        if not tasks:
            return "(no tasks yet)"
        lines = []
        for t in tasks:
            mark = "x" if t.done else " "
            lines.append(f"[{mark}] #{t.id} {t.title}")
        return "\n".join(lines)

    def render_single(self, task: Task) -> str:
        mark = "x" if task.done else " "
        return f"[{mark}] #{task.id} {task.title}"

    def render_error(self, message: str) -> str:
        return f"ERROR: {message}"


# ---------------------------------------------------------------------------
# CONTROLLER — receives input, orchestrates Model calls, picks a View.
# This is the "glue" layer. In a real app this would be a Flask/Django/
# FastAPI route handler.
# ---------------------------------------------------------------------------
class TaskController:
    def __init__(self, model: TaskModel, view):
        self._model = model
        self._view = view

    def handle_create(self, title: str):
        try:
            task = self._model.create_task(title)
            print(f"[Controller] POST /tasks title={title!r} -> 201")
            return self._view.render_single(task)
        except ValueError as e:
            print(f"[Controller] POST /tasks title={title!r} -> 400")
            return self._view.render_error(str(e))

    def handle_complete(self, task_id: int):
        try:
            task = self._model.complete_task(task_id)
            print(f"[Controller] POST /tasks/{task_id}/complete -> 200")
            return self._view.render_single(task)
        except KeyError as e:
            print(f"[Controller] POST /tasks/{task_id}/complete -> 404")
            return self._view.render_error(str(e))

    def handle_list(self):
        tasks = self._model.list_tasks()
        print("[Controller] GET /tasks -> 200")
        return self._view.render_list(tasks)


# ---------------------------------------------------------------------------
# Demo — same Model + same Controller class, driven through two different
# Views to prove presentation is fully decoupled from logic.
# ---------------------------------------------------------------------------
def _demo():
    model = TaskModel()

    print("=== Using JsonTaskView (simulating a REST API) ===")
    json_controller = TaskController(model, JsonTaskView())
    print(json_controller.handle_create("Write MVC demo"))
    print(json_controller.handle_create("Review PR"))
    print(json_controller.handle_complete(1))
    print(json_controller.handle_list())
    print(json_controller.handle_complete(999))  # not found

    print("\n=== Using PlainTextTaskView (same Model, CLI-style output) ===")
    text_controller = TaskController(model, PlainTextTaskView())
    print(text_controller.handle_list())


if __name__ == "__main__":
    _demo()
