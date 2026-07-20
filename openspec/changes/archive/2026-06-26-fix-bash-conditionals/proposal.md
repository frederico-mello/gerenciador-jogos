## Why

SonarCloud flagged 10 `shelldre:S7688` MAJOR issues across `deploy/setup.sh` (9) and `scripts/run-as-app.sh` (1) for using single-bracket `[` conditional tests instead of double-bracket `[[`. The `[[` construct is safer (no word splitting, no pathname expansion) and more feature-rich (supports `&&`, `||`, `=~` regex). This is a well-established shell scripting best practice for Bash.

## What Changes

- Replace all `[ ... ]` conditional expressions with `[[ ... ]]` in both shell scripts
- Adjust `]` to `]]` in the closing bracket position
- No logic changes — pure syntax upgrade

## Capabilities

### New Capabilities
- `bash-safe-conditionals`: Shell scripts use `[[ ]]` for all conditional tests, following Bash best practices.

### Modified Capabilities
<!-- None — syntax-only change, no behavioral impact. -->

## Impact

- Affected files: `deploy/setup.sh` (9 sites, lines 12, 34, 44, 46, 64, 86, 100, 116, 136), `scripts/run-as-app.sh` (1 site, line 15)
- No behavioral changes.
