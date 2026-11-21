# Living spec

A living spec says what the system does now, for one capability. It changes only when a change's delta is merged into
it (see [delta.md](delta.md) for when that happens). A project that starts with Keellay on existing code begins with
no specs; a capability gets its spec with the first change that touches it, from level standard up.

## File

`docs/specs/<capability>.md`, one per capability. A capability is a piece of behaviour a user or another system can
observe, named in lowercase words joined by hyphens: `auth-session`, `export-csv`, `cli`.

```markdown
---
capability: auth-session
prefix: auth
---

# Auth session

What this capability is for and where its boundary is, in a few sentences.

## Requirements

### REQ-auth-003: Session expires after inactivity

When a session has had no requests for the configured timeout, the service shall end the session.

Verified by: `tests/session/test_expiry.py::test_inactive_session_ends`

#### Scenario: inactive session

- GIVEN a session with a 30-minute timeout
- WHEN no request arrives for 30 minutes
- THEN the next request is answered with "session expired"

#### Scenario: activity extends the session

- GIVEN a session with a 30-minute timeout
- WHEN a request arrives after 20 minutes
- THEN the session stays open for another 30 minutes
```

## Requirement

- **ID:** `REQ-<prefix>-<nnn>`. The prefix is set once per spec; numbers are sequential within the spec and never
  reused, also after a requirement is removed. The ID is the merge key for deltas.
- **Title:** what the requirement guarantees, as a short sentence.
- **Statement:** one sentence in EARS form, with "shall":

| Pattern | Form |
|---|---|
| Ubiquitous | The `<system>` shall `<response>`. |
| Event | When `<trigger>`, the `<system>` shall `<response>`. |
| State | While `<state>`, the `<system>` shall `<response>`. |
| Unwanted | If `<condition>`, then the `<system>` shall `<response>`. |
| Optional | Where `<feature>`, the `<system>` shall `<response>`. |

- **Scenarios:** at least one, as GIVEN (optional) / WHEN / THEN lines; AND continues the line above it. Each scenario
  should be checkable by a test.
- **Verified by:** tests that check the requirement. Optional at level standard, required at strict; level light
  has no living specs.

## Index: docs/specs/README.md

```markdown
# Specs

What the system does now, one file per capability.

| Capability | Covers |
|---|---|
| [auth-session](auth-session.md) | Session lifetime and expiry |
```

## Checked by

`keellay check` (planned): one index row per spec; front matter; IDs are unique, use the spec's prefix and are not
reused (compared with git history); every requirement has a statement with "shall" and at least one scenario; at
strict, every requirement has a "Verified by" line pointing to an existing test.
