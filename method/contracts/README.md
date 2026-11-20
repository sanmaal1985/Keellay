# Role contracts

A contract defines what a role skill must contain — required sections, fixed rules, references — without saying
anything about a particular project. Every project gets the four core roles, generated from these contracts; more
roles are added only as instances of a core contract (for example `developer-flutter`) or from contracts in this
catalogue, with the owner's yes.

| Contract | Kind | Status |
|---|---|---|
| `product-owner` | core | planned |
| `architect` | core | planned |
| `developer` | core | planned |
| `manager` | core | planned |

## Contract file

`method/contracts/<role>.md`, one per role. A project may write its own contract for a role the catalogue does not
have; it follows the same schema and is added with the owner's yes.

```markdown
---
role: architect          # the name plan phases use; lowercase words joined by hyphens
kind: core               # core | catalogue
version: 1               # raised when a fixed part changes
---

# Architect

## Purpose
## When active
## Owns
## Hands off
## Rules
## Project sections
## References
## Scenarios
```

All sections are required, in this order.

| Section | Holds | In the generated skill |
|---|---|---|
| Purpose | what the role does and where its boundary is, in one or two sentences | the first part of `description`; not repeated in the body |
| When active | the situations that call the role — a plan phase tagged with it, a kind of owner request, a status — in the words real requests use | the second part of `description` ("Use when …"); not repeated in the body |
| Owns | a table of the artifacts the role writes, the status changes it makes and the gates it holds | fixed |
| Hands off | who takes over, at which point, with what | fixed |
| Rules | numbered rules for this role, each marked `[check]` or `[instruction]` | fixed, word for word |
| Project sections | a table of the sections filled for each project (see below) | filled per project |
| References | the formats and procedures the role works with, each with when to read it | copied into the skill's `references/` |
| Scenarios | trigger queries and behaviour scenarios (see below) | not copied; they become the skill's evals |

How contracts are written:

- **Only what an agent would not know.** No general advice on design, coding or product work; a capable agent has
  it already. A contract holds the method's rules and points to the project's evidence.
- **Instructions, not a persona.** No "you are an architect"; a contract says what to do, when and with what.
- **One term per concept**, the terms of the formats: change, phase, delta, living spec, lesson.
- **Rules every role follows** — claims only from files, choices are the owner's, open questions listed — are in the
  constitution, not repeated in contracts. A contract's Rules hold only what is specific to the role.
- **Each rule says how it holds.** `[check]`: a check in hooks or CI enforces it, and the rule names the check.
  `[instruction]`: only the text holds it. A rule that keeps being broken moves from instruction to check through a
  lesson.

### Project sections

Each row is one section of the skill that the agent fills for the project, from evidence in the repository:

```markdown
| Section | Holds | Evidence | Ask the owner |
|---|---|---|---|
| Build and test | commands that build the project and run its tests | build files, CI workflows, README | which command is the one to trust, when several disagree |
```

- **Evidence** says where to look; the agent fills the section from what it finds there, not from general knowledge.
- **Ask the owner** says what to ask when the evidence is missing or contradicts itself. Nothing is guessed.
- A section the project does not need is filled with one line saying why, so the check can tell it from a forgotten
  one.

### Scenarios

Written before the rest of the contract: they say what the role must get right, and the text is the least that makes
them pass.

**Triggers.** Requests that should call the role, and near misses that should not — requests with similar words that
belong to another role:

```markdown
### Triggers

| Request | Calls this role |
|---|---|
| Plan the session-expiry feature | yes |
| Should this be a fix or a change? | yes |
| Fix the typo on the login screen | no — developer |
| Is session expiry worth building? | no — product-owner |
```

Three to five of each. Near misses come from the other roles first: they are where selection goes wrong.

**Behaviour.** Three to five scenarios, written like spec scenarios. Each one describes behaviour someone can observe
in the agent's output — what it writes, does or declines to do — not an intention:

```markdown
### Scenario: open question holds dependent work

- GIVEN two questions are open and the owner answered one
- WHEN the next step depends on the other question
- THEN the agent does not start that step
- AND lists the open question at the end of its message
```

A rule that came from a lesson has at least one behaviour scenario.

## Instances

`<core role>-<qualifier>`, for example `developer-flutter` and `developer-backend` in a repository with two stacks.
An instance follows its core contract: the same fixed parts, its own project sections, filled for its part of the
repository. Plan phases may name an instance or the core role.

## Skill from a contract

The generated skill is a folder in the open Agent Skills format, named after the role:

```
architect/
  SKILL.md
  references/
    change.md           copied from method/formats/
    delta.md
```

```markdown
---
name: architect
description: Plans changes, ... Use when ...
metadata:
  keellay-contract: architect
  keellay-contract-version: "1"
---

## Owns
## Hands off
## Rules
## <project sections>
## References
```

- **Front matter** has only the fields of the Agent Skills format; Keellay's own data goes under `metadata`. Fields
  that one agent understands, such as when a skill may load itself, are added by that agent's wiring.
- **`description`** is Purpose followed by "Use when" and When active, at most 1024 characters.
- **The body** starts with Owns: no title that repeats the name, no restated description. It stays under 500 lines;
  anything longer goes to `references/`.
- **References** are one level deep: each file sits in `references/`, and the References section lists each with a
  line saying when to read it.

The CLI renders the skeleton — front matter, the fixed sections, the headings of the project sections, the copied
references — and records the contract and its version in `.keellay/manifest.json`. The agent fills the project
sections. On upgrade the CLI re-renders the fixed parts and keeps the filled ones. How filled sections are marked
and how scenarios run as evals belong to the role generation procedure (planned).

## Checked by

`keellay check` (planned).

- Contracts: front matter fields and values; all sections present and in order; every Owns row matches the
  responsibility table; every rule marked `[check]` or `[instruction]`, every `[check]` rule names its check; every
  project section has Evidence and Ask the owner; three to five triggers of each kind; three to five behaviour
  scenarios, each with WHEN and THEN.
- Generated skills: front matter valid for the Agent Skills format; `description` within 1024 characters; body under
  500 lines; no fill markers left; no names from other projects; every file in `references/` listed in References.
