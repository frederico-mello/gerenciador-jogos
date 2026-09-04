## Context

`deploy/setup.sh` and `scripts/run-as-app.sh` are Bash scripts used for server deployment and production script execution. They use `[` (an alias for the `test` command) for conditionals, which SonarCloud rule `shelldre:S7688` flags as a best-practice violation in favor of `[[` (a Bash keyword).

Single-bracket `[` has known pitfalls:
- Word splitting applies to unquoted variables inside `[`
- No support for `&&`/`||` as logical operators (must use `-a`/`-o`)
- No regex matching
- Pathname expansion

Double-bracket `[[` eliminates these issues and is available in all modern Bash versions.

## Goals / Non-Goals

**Goals:**
- Replace all `[ ]` with `[[ ]]` in both shell scripts
- Preserve exact same logic and flow

**Non-Goals:**
- Adding shellcheck or other linting
- Refactoring the script logic

## Decisions

### 1. Direct mechanical substitution

**Decision**: Replace `[ expr ]` with `[[ expr ]]` and `]` with `]]` on the same lines. No restructuring of condition chains.

**Rationale**: The simplest, safest change. Since `[[` is a superset of `[` functionality, the same expressions work without modification.

### 2. Handle `=` operator in single brackets

**Decision**: The `=` operator inside `[` is a string comparison and remains valid inside `[[`. No change to operators needed.

**Rationale**: `[[` supports `=` for string comparison. The scripts don't use `==` which would also be valid.

## Risks / Trade-offs

- **Bash version**: `[[` requires Bash (not POSIX sh). → Mitigation: Both scripts already use `#!/bin/bash` shebang, so no compatibility issue.
- **Whitespace**: `[[` requires a space after `[[` and before `]]`, same as `[`. No change in spacing habits needed.
