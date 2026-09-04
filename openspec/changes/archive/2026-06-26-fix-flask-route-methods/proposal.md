## Why

SonarCloud flagged 11 `python:S6965` issues in `app/routes.py` — Flask routes that use `@app.route()` without specifying `methods`. When methods are unspecified, Flask defaults to `GET` only. Mutating routes (POST handlers, delete handlers) that omit explicit methods may work via form submission but are semantically incomplete and could be reached via GET unexpectedly. Explicit methods are a security best practice and a SonarCloud Clean Code requirement.

## What Changes

- Add explicit `methods=["GET"]` or `methods=["GET", "POST"]` or `methods=["POST"]` to all 11 route decorators in `app/routes.py` that currently lack a methods parameter
- Review each route function body to determine which methods it actually handles and declare accordingly

## Capabilities

### New Capabilities
- `explicit-route-methods`: All Flask route decorators explicitly declare their accepted HTTP methods.

### Modified Capabilities
<!-- None — explicit declaration doesn't change behavior, only makes existing behavior explicit. -->

## Impact

- Affected file: `app/routes.py` only (11 decorators at lines 90, 145, 203, 295, 386, 537, 583, 673, 727, 854, 930)
- No API, dependency, or behavior changes.
