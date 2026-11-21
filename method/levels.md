# Strictness levels and change paths

Ceremony is set on two axes. The **project level** decides which mechanisms are installed and sets the floor. The
**change path** decides what one change goes through; the architect proposes it and the owner confirms.

## Project levels

Each level adds to the one above.

| Level | Turns on |
|---|---|
| light | constitution linked from `AGENTS.md`, core roles, PRD and ideas register, changes and plans without deltas, fresh-context review at close, ADRs and index, lessons and index, owner gates; hooks: index co-change, doc links |
| standard (default) | living specs and deltas for behaviour changes, plans with role-tagged phases and done-when, the fresh-context review also reads the merged specs, retro after each closed plan; CI runs the same checks as the hooks |
| strict | a delta for every behaviour change (enforced in CI), spec freshness gate, fresh-context review for every change including fixes, skill evals in CI, configurable code-rule gates |

An existing project usually starts at light and moves up through an ADR.

## Change paths

| Path | When | Artifacts |
|---|---|---|
| fix | a defect with known expected behaviour | bugfix triple (current / expected / unchanged) and a test; no plan |
| change | small, one area, low risk | short plan; a delta if behaviour changes |
| feature | a new capability, several areas, or high risk | idea or PRD entry → plan with phases → delta → waves → fresh-context review → close |

At level light there are no living specs, so no path writes a delta; the fresh-context review at close runs at every
level.
