## Context

Flask's `@app.route()` decorator accepts an optional `methods` parameter. When omitted, the route defaults to `GET` only. The project has 11 routes in `app/routes.py` that omit `methods`. Most of these are likely `GET`-only (page renders), but without explicit declaration, a reviewer cannot tell at a glance whether POST access is intentional or an oversight.

SonarCloud rule `python:S6965` flags this as a MAJOR Code Smell with clean code attribute `CONVENTIONAL`.

## Goals / Non-Goals

**Goals:**
- Add explicit `methods` parameter to all 11 affected route decorators
- Determine the correct method for each route by inspecting the function body
- Make route behavior explicit and auditable

**Non-Goals:**
- Changing any route's behavior
- Adding new routes or removing existing ones

## Decisions

### 1. Method determination by inspection

**Decision**: Read each route function's body to determine what it does. Functions that:
- Render templates only → `methods=["GET"]`
- Handle form submissions (check `request.method == "POST"`) → `methods=["GET", "POST"]`
- Are pure mutation endpoints (e.g., POST-only actions) → `methods=["POST"]`

**Rationale**: Deriving from actual code prevents accidental restriction that breaks existing pages.

### 2. Apply to all 11 routes uniformly

**Decision**: Fix all 11 S6965 issues in a single pass rather than selectively.

**Rationale**: Consistency — all routes should declare methods. Partial fixes would leave the remaining issues open in SonarCloud.

## Risks / Trade-offs

- **Method mismatch risk**: If a route function handles POST but we declare only GET, form submissions break. → Mitigation: Thorough function body reading before declaring; run full test suite after.
