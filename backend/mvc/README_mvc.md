# MVC Pattern (Model-View-Controller)

**Category:** Backend / Architectural
**File:** `mvc.py`

## Intent

Split an application into three responsibilities:

- **Model** — data + business rules. Knows nothing about how it's displayed.
- **View** — presentation/formatting. Knows nothing about business rules.
- **Controller** — receives input, orchestrates calls to the Model, picks
  a View to render the result. The "glue."

The point is **separation of concerns**: change how data is displayed
without touching business logic, and vice versa.

## When to use it

- Basically every web framework (Django, Rails, Spring MVC, ASP.NET MVC)
  is built around this pattern
- Any app that needs to render the same underlying data in multiple ways
  (JSON API + HTML page + CLI output)
- Keeping route handlers thin — logic lives in the Model, not scattered
  across controllers

## How it works (this file)

- `TaskModel` — owns `Task` data and rules (`create_task`,
  `complete_task`, `list_tasks`). Raises plain exceptions
  (`ValueError`, `KeyError`) — no HTTP status codes here, that's not its job.
- `JsonTaskView` / `PlainTextTaskView` — two interchangeable views. Same
  data, two totally different output shapes (dict for an API,
  formatted string for a CLI).
- `TaskController` — simulates route handlers (`handle_create`,
  `handle_complete`, `handle_list`). Talks to the Model, catches domain
  exceptions, translates them to a response via whichever View it was
  given.

The demo drives the **same** `TaskModel` and `TaskController` class
through two different `View` implementations to prove the presentation
layer is fully swappable.

## Key interview talking points

- **Where MVC breaks down at scale:** "Fat controllers" — teams often
  dump business logic into controllers because it's the easiest place to
  add code. The fix is keeping controllers thin (orchestration only) and
  pushing logic into the Model or a dedicated service layer (see Facade /
  Repository patterns — they often sit *inside* the Model layer of an
  MVC app).
- **MVC vs. MVVM vs. MVP:** all are variations on separating
  data/logic/presentation; the difference is mainly *how* the View and
  the data layer communicate (MVC: Controller mediates; MVVM: View binds
  to a ViewModel; MVP: Presenter mediates and the View is passive).
- **Backend vs. frontend MVC:** backend MVC (Django/Rails) renders a
  response per request; frontend MVC/MVVM (older Angular, Backbone)
  keeps state in memory across interactions. Different lifecycles, same
  separation principle.
- **Testability:** because `TaskModel` has zero view/HTTP knowledge, you
  can unit test all business rules without spinning up a web server or
  parsing JSON.

## Run it

```bash
python3 mvc.py
```
