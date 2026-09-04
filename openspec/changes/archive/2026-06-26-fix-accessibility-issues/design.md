## Context

The project uses Bootstrap for styling and Jinja2 templates for rendering. SonarCloud's web accessibility rules flag several WCAG violations across templates and CSS:

1. **InputWithoutLabelCheck (5 issues, MAJOR/BUG)**: Search/filter inputs lack `id` attributes, preventing `<label>` association. Screen readers cannot identify these controls.
2. **S6821 invalid ARIA roles (3 issues, MAJOR)**: `admin_users.html` uses non-standard values `"admin_sistema"`, `"admin_jogos"`, `"usuario"` as ARIA role attributes. These are not valid WAI-ARIA roles.
3. **S7924 contrast (2 issues, MAJOR)**: Text at `style.css:101` and `:558` does not meet the 4.5:1 contrast ratio required by WCAG AA.
4. **S6819 semantic element (2 issues, MAJOR)**: Using `<div role="status">` instead of `<output>` and `<div role="dialog">` instead of `<dialog>`.
5. **LinksIdenticalTextsDifferentTargets (1 issue, MAJOR)**: Same link text pointing to different URLs.

## Goals / Non-Goals

**Goals:**
- Add `id` attributes to all search/filter inputs and label them properly
- Fix or remove invalid ARIA role values
- Adjust CSS colors to meet WCAG AA contrast
- Replace div+role with native semantic HTML elements
- Differentiate duplicate link text

**Non-Goals:**
- Full WCAG AAA compliance audit
- Replacing Bootstrap with a different framework
- Adding automated accessibility testing

## Decisions

### 1. Input label strategy

**Decision**: For search/filter inputs that currently lack `<label>`, add `id` to the input and a `<label for="...">` before or after it. For visually hidden labels (search inputs with placeholder text), use a `<label>` with Bootstrap's `visually-hidden` class.

**Rationale**: Proper label association is the most impactful accessibility fix. Screen readers announce the label when the input is focused. Bootstrap's `visually-hidden` class keeps the UI visually unchanged while providing the label to assistive technology.

### 2. ARIA role fix

**Decision**: Determine the INTENT of `role="admin_sistema"` etc. If these are custom data attributes (not ARIA), replace with `data-role="..."`. If they're genuinely attempting to set ARIA roles, remove the invalid values.

**Rationale**: The values `"admin_sistema"`, `"admin_jogos"`, `"usuario"` look like application-level user role names, not ARIA roles. Converting to `data-role` preserves the information without violating the spec.

### 3. Contrast fix

**Decision**: Inspect the actual color pairs at lines 101 and 558 of `style.css` and adjust either the text color or background to achieve at least 4.5:1 contrast ratio.

**Rationale**: Color adjustments are low-risk CSS changes. Use a contrast checker (e.g., WebAIM) to verify the new colors.

### 4. Semantic HTML elements

**Decision**: Replace `<div role="status">` with `<output>` (base.html:41) and `<div role="dialog">` with `<dialog>` (detail.html:156). Add polyfill attributes if needed for older browsers.

**Rationale**: Native HTML elements carry implicit ARIA semantics and are better supported than manually applied roles. `<output>` and `<dialog>` are well-supported in modern browsers (Chrome 10+, Firefox 4+, Safari 6+).

### 5. Link text differentiation

**Decision**: Inspect the duplicate link text in `form.html` and add visually hidden descriptive text or modify the visible text to distinguish the targets.

**Rationale**: Screen reader users navigating by links hear identical text for different targets, creating confusion. The fix is usually adding context like "Edit [name]" vs "Delete [name]".

## Risks / Trade-offs

- **Bootstrap compatibility**: Replacing `<div>` with `<output>` or `<dialog>` may conflict with Bootstrap's CSS selectors. → Mitigation: Add Bootstrap-compatible classes or adjust styles.
- **Color changes**: May affect visual design intent. → Mitigation: Choose colors close to the original that meet contrast requirements.
