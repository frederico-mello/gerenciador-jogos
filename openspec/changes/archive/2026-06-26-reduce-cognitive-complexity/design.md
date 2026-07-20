## Context

Cognitive complexity measures how hard it is to understand a function by counting nesting, conditionals, loops, and other control flow structures. SonarCloud's threshold is 15. The project has 8 functions exceeding this, all in route handlers and CLI scripts — code that tends to accumulate validation, branching, and side effects.

The core pattern in `app/routes.py` is shared across multiple functions:
1. Check authentication and authorization (multiple `if` branches for roles)
2. Validate form input (multiple `if` branches for each field)
3. Process the request (database calls, file handling)
4. Set flash messages and redirect

This pattern naturally accumulates complexity because each step adds nested conditionals.

## Goals / Non-Goals

**Goals:**
- Reduce all 8 functions to cognitive complexity ≤ 15
- Preserve existing behavior exactly (all tests pass)
- Extract reusable validation and authorization helpers

**Non-Goals:**
- Rewriting the entire routes.py architecture
- Changing the form handling framework (Flask-WTF is not being introduced)
- Reducing cognitive complexity of other functions below 15

## Decisions

### 1. Extract-by-responsibility refactoring

**Decision**: For each route handler, extract three categories of helper functions:
- **Validation helpers**: functions that validate form fields and return error lists
- **Authorization helpers**: functions that check user role and return early with redirect if blocked
- **Processing helpers**: functions that perform the actual database/file operation

**Rationale**: Each extracted function handles one concern, has low complexity itself, and is independently testable. The route handler becomes a coordinator: check auth, validate, process, respond.

**Alternative considered**: Using decorators for auth checks. Rejected because auth logic varies by route (different role requirements, different redirect targets). Helper functions give explicit control.

### 2. Helper function placement

**Decision**: Place extracted helper functions in the same `app/routes.py` file as module-level functions (not in a separate module). For `create_admin.py`, keep helpers within the same script.

**Rationale**: Keeps the change self-contained within the affected files. Avoids creating new modules that would need import management. If the helpers prove reusable across multiple route files, they can be promoted later.

### 3. Complexity target: 15 per function (strict)

**Decision**: Aim for cognitive complexity ≤ 15 in EACH function, not just an average.

**Rationale**: The SonarCloud rule evaluates functions individually. The Quality Gate monitors the count of S3776 issues — each function above 15 is one issue. To clear all 8 issues, every function must be ≤ 15.

### 4. Refactoring strategy for the worst offender (create_user, complexity 27)

The `create_user` function at line 464 is the most complex at 27. The strategy:
1. Extract `_validate_user_form(form, is_edit=False)` — handles all field validation (name, email, password, role)
2. Extract `_check_admin_access(user, required_role)` — handles role-based authorization with flash message and redirect
3. Extract `_create_user_record(form)` — handles the database insertion
4. The route handler becomes: auth check → validate → create → flash → redirect

**Rationale**: Each extracted function should have complexity ≤ 5. The route handler (coordinator) should be ≤ 8. This clears the bar.

## Risks / Trade-offs

- **Behavior change risk**: Extracting helpers can accidentally change variable scope, return values, or side effects. → Mitigation: Run full test suite after each function refactoring, not just at the end.
- **Over-extraction**: Creating too many tiny helpers can hurt readability. → Mitigation: Extract only when the extracted function is conceptually coherent (validation, auth, processing). Don't extract 2-line fragments.
- **Template resolution**: Helper functions must have access to `url_for` and `render_template`. → Mitigation: These are Flask globals, so module-level helpers can call them directly.
