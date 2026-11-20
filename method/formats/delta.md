# Spec delta

A delta is the intended change to one living spec, written inside a change before the code. It is reviewed as a diff
of behaviour, and when the change closes the CLI merges it into the spec by requirement ID.

## File

`docs/changes/<change-id>/delta/<capability>.md`, one per capability the change touches.

```markdown
---
capability: auth-session
---

# Delta: auth-session

## ADDED

### REQ-auth-004: Expired session is reported once

If a request arrives for an expired session, then the service shall answer "session expired" and drop the session
token.

#### Scenario: request after expiry

- WHEN a request arrives for an expired session
- THEN the answer is "session expired" and the token is no longer accepted

## MODIFIED

### REQ-auth-003: Session expires after inactivity

(the full new text of the requirement: statement, Verified by, scenarios)

## REMOVED

### REQ-auth-002: Session lasts 24 hours

Reason: replaced by the inactivity timeout in REQ-auth-003.
```

- **ADDED** and **MODIFIED** carry the full text of each requirement, not a patch, so the result can be read without
  the old spec.
- **REMOVED** carries the ID, the title and the reason.
- A new number for ADDED is the next free one in the spec; numbers taken by other open changes count as taken.
- **New capability:** when no spec exists yet, the delta also has a `## Purpose` section, and on merge it becomes the
  new spec with `prefix` in its front matter.
- Sections that would be empty are left out.

## Merge at close

1. The CLI applies the delta: ADDED requirements are appended, MODIFIED ones replace the requirement with the same
   ID, REMOVED ones are deleted.
2. The CLI validates the result: every ADDED and MODIFIED ID is present with the delta's text, every REMOVED ID is
   gone, and no ID touched here is also touched by another open change.
3. A fresh-context architect session reads the merged spec against the code and tests and records the result in the
   plan's Close section.

## Checked by

`keellay check` (task 4): every MODIFIED and REMOVED ID exists in the living spec; every ADDED ID does not; no two
open changes touch the same ID (reported when the second delta is written); the requirement rules from
[spec.md](spec.md) hold for ADDED and MODIFIED.
