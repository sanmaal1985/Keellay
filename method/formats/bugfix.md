# Bugfix

The fix path is for a defect whose expected behaviour is already known: the system does not do what its spec, or
plain common sense, says it should. It needs no change folder and no plan. If fixing it means deciding new behaviour,
it is not a fix: open a change.

## The triple

Written in the body of the fix commit's message, so it lives in git and a hook or CI on any host can check it. A pull
request description may repeat it.

```markdown
Current: When a session has been idle for 30 minutes, the next request still succeeds.
Expected: The request is answered with "session expired" (REQ-auth-003).
Unchanged: A session with a request every 20 minutes stays open.
```

- **Current:** what the system does now, reproducibly.
- **Expected:** what it should do, with the requirement ID when a spec covers it.
- **Unchanged:** behaviour near the defect that must stay as it is. Each line becomes a regression test next to the
  test for the fix.

## Rules

- A test that fails before the fix and passes after it.
- No delta: the spec already says what is expected, or the spec gains a requirement through a change, not through a
  fix.
- Branch: `fix/<topic>`.
- At level strict, a fix also gets a fresh-context review.

## Checked by

`keellay check` (task 4): on a `fix/` branch, a commit message has the Current, Expected and Unchanged lines. The
test rules are for the review.
