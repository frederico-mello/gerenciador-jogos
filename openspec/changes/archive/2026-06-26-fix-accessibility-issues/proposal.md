## Why

SonarCloud flagged 13 accessibility issues across templates and CSS: input fields without associated labels (5), invalid ARIA roles (3), insufficient text contrast (2), semantic HTML elements used as ARIA roles instead of native elements (2), and identical link text pointing to different targets (1). These issues affect users relying on screen readers, keyboard navigation, and users with visual impairments.

## What Changes

- **Templates**: Add `id` attributes to input fields and associate them with `<label>` elements
- **admin_users.html**: Replace invalid ARIA role values (`"admin_sistema"`, `"admin_jogos"`, `"usuario"`) with valid Bootstrap roles or remove them
- **base.html**: Replace `<div role="status">` with native `<output>` element
- **detail.html**: Replace `<div role="dialog">` with native `<dialog>` element
- **style.css**: Adjust text/background color combinations at lines 101 and 558 to meet WCAG AA contrast ratio (4.5:1 for normal text)
- **form.html**: Differentiate link text for links pointing to different targets

## Capabilities

### New Capabilities
- `web-accessibility`: Templates and styles meet WCAG AA accessibility standards for labels, contrast, semantic HTML, and ARIA usage.

### Modified Capabilities
<!-- None — UI updates, no behavioral changes. -->

## Impact

- Affected files: `app/templates/admin_users.html`, `app/templates/admin_schools.html`, `app/templates/emprestimos_admin.html`, `app/templates/base.html`, `app/templates/detail.html`, `app/templates/form.html`, `app/static/style.css`
- No API or behavior changes.
