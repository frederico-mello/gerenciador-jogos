## ADDED Requirements

### Requirement: Input fields have associated labels
All `<input>` elements in templates SHALL have an `id` attribute and be associated with a `<label for="...">` element, or use `aria-label`/`aria-labelledby` as a fallback.

#### Scenario: Search input has associated label
- **WHEN** a search/filter input is rendered on the page
- **THEN** a screen reader announces the input's label when the input receives focus

### Requirement: ARIA roles use valid values
All `role` attributes in templates SHALL contain only valid WAI-ARIA role values. Application-specific metadata SHALL use `data-*` attributes instead.

#### Scenario: Invalid ARIA role is replaced
- **WHEN** `admin_users.html` renders user role badges
- **THEN** the `role` attribute uses a valid ARIA role value or the attribute is replaced with `data-role`

### Requirement: Text meets WCAG AA contrast ratio
All text content in `style.css` SHALL have a contrast ratio of at least 4.5:1 against its background, meeting WCAG AA Level.

#### Scenario: Contrast at line 101 meets AA
- **WHEN** text styled by the rule at `style.css:101` is rendered
- **THEN** the contrast ratio between text and background is ≥ 4.5:1

### Requirement: Semantic HTML elements are used instead of div+role
Where native HTML elements provide equivalent semantics, templates SHALL use the native element instead of `<div role="...">`.

#### Scenario: Status region uses output element
- **WHEN** `base.html` renders status information
- **THEN** it uses `<output>` instead of `<div role="status">`

### Requirement: Identical link text differentiates targets
Links with identical visible text SHALL point to the same target URL, or the visible text SHALL be differentiated.

#### Scenario: Duplicate link text is resolved
- **WHEN** `form.html` renders multiple action links
- **THEN** links pointing to different targets have distinguishable text
