# Spec delta

A delta is the intended change to one living spec, written for a change before the code. It is reviewed as a diff of
behaviour, and the CLI merges it into the spec by requirement ID: when the change goes to `review`, or in the
implementing pull request when plans and specs are in different repositories (see File).

## File

`docs/changes/<change-id>/delta/<capability>.md`, one per capability the change touches.

**Plans and specs in different repositories.** A delta lives next to the specs it changes. When a project keeps its
plans in another repository than its specs, the delta goes to the same path in the specs' repository, and the merge
below runs in the pull request that implements it, before that pull request is merged, so the spec changes in the
same commit as the code. The same pull request moves the merged delta to `docs/changes/archive/<change-id>/`, so it
is not mistaken for the delta of an open change. The fresh-context review at close then reads the already merged
spec. The plan links the delta and records the merging commit in Close.

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
- **New capability:** when no spec exists yet, the delta's front matter also has `prefix`, and the delta has a
  `## Purpose` section. On merge it becomes the new spec: `capability` and `prefix` in its front matter, the Purpose
  text as the untitled opening text under the title, then the requirements.
- Sections that would be empty are left out.

## Merge

When plans and specs share a repository, the merge runs when the change goes to `review`; otherwise in the
implementing pull request (see File).

1. The CLI applies the delta: ADDED requirements are appended, MODIFIED ones replace the requirement with the same
   ID, REMOVED ones are deleted.
2. The CLI validates the result: every ADDED and MODIFIED ID is present with the delta's text, every REMOVED ID is
   gone, and no ID touched here is also touched by another open change.
3. The fresh-context architect session at close reads the merged spec against the code and tests and records the
   result in the plan's Close section.

## Checked by

`keellay check` (planned): every MODIFIED and REMOVED ID exists in the living spec; every ADDED ID does not; no two
open changes touch the same ID (reported when the second delta is written); the requirement rules from
[spec.md](spec.md) hold for ADDED and MODIFIED.
