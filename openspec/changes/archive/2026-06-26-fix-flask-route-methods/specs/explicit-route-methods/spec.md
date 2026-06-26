## ADDED Requirements

### Requirement: All Flask routes declare accepted HTTP methods
Every `@app.route()` decorator in `app/routes.py` SHALL include an explicit `methods` parameter listing the HTTP methods the route accepts.

#### Scenario: GET-only routes declare GET
- **WHEN** a route function only renders a template and does not inspect `request.method`
- **THEN** the decorator includes `methods=["GET"]`

#### Scenario: Form-handling routes declare GET and POST
- **WHEN** a route function inspects `request.method == "POST"` to handle form submissions and also renders a template for GET
- **THEN** the decorator includes `methods=["GET", "POST"]`

#### Scenario: SonarCloud no longer flags missing methods
- **WHEN** SonarCloud re-analyzes `app/routes.py`
- **THEN** rule `python:S6965` fires on zero lines
