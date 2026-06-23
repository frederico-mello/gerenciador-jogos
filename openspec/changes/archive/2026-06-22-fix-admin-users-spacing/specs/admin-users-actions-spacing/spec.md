## ADDED Requirements

### Requirement: Actions column spacing
The system SHALL render the actions column in the admin users table with consistent spacing between controls (buttons, links, selects).

#### Scenario: Controls are visually separated
- **WHEN** an admin views the users table
- **THEN** each control in the "Ações" column (Editar link, role select, Inativar/Reativar button) SHALL have at least 8px of horizontal gap between them.

#### Scenario: Controls wrap on narrow screens
- **WHEN** the viewport is narrower than 600px
- **THEN** the actions controls SHALL wrap to multiple lines without overlapping.

### Requirement: Toolbar uses project patterns
The system SHALL render the page toolbar (filters + "Novo usuário" button) using the existing layout patterns from the project.

#### Scenario: Toolbar uses list-header layout
- **WHEN** an admin visits `/admin/users`
- **THEN** the toolbar SHALL use the `.list-header` class for horizontal layout with space-between alignment.

#### Scenario: Filter form uses standard styling
- **WHEN** an admin views the toolbar
- **THEN** the role filter form SHALL use `.filter-form` class for consistent padding and border styling.

### Requirement: No functional changes
The system SHALL preserve all existing behavior (form submissions, CSRF tokens, filter functionality, role changes, inactivate/reactivate actions).

#### Scenario: Filter still works
- **WHEN** an admin selects a role from the filter dropdown
- **THEN** the form SHALL submit and filter results as before.

#### Scenario: Inactivate still works
- **WHEN** an admin clicks "Inativar"
- **THEN** the POST request SHALL be sent with the correct CSRF token and user ID.
