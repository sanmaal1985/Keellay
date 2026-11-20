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
| Purpose | what the role is for and where its boundary is, in a few sentences | fixed; with When active, it becomes the skill's `description` |
| When active | the situations that call the role: a plan phase tagged with it, a kind of owner request, a status | fixed |
| Owns | a table of the artifacts the role writes, the status changes it makes and the gates it holds | fixed |
| Hands off | who takes over, at which point, with what | fixed |
| Rules | numbered rules for this role, each one checkable by a scenario | fixed, word for word |
| Project sections | a table of the sections filled for each project (see below) | filled per project |
| References | the formats and procedures the role works with | fixed; paths resolved for the project |
| Scenarios | behaviour scenarios (see below) | not copied; they become the skill's evals |

Rules every role follows — claims only from files, choices are the owner's, open questions listed — are in the
constitution, not repeated in contracts. A contract's Rules hold only what is specific to the role.

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

Three to five per role, written like spec scenarios. Each one describes behaviour someone can observe in the agent's
output — what it writes, does or declines to do — not an intention:

```markdown
### Scenario: open question holds dependent work

- GIVEN two questions are open and the owner answered one
- WHEN the next step depends on the other question
- THEN the agent does not start that step
- AND lists the open question at the end of its message
```

A rule that came from a lesson has at least one scenario.

## Instances

`<core role>-<qualifier>`, for example `developer-flutter` and `developer-backend` in a repository with two stacks.
An instance follows its core contract: the same fixed parts, its own project sections, filled for its part of the
repository. Plan phases may name an instance or the core role.

## Skill from a contract

The CLI renders the skill's skeleton from the contract — front matter, the fixed sections, the headings of the
project sections — and records the contract and its version in `.keellay/manifest.json`. The agent fills the project
sections. On upgrade the CLI re-renders the fixed parts and keeps the filled ones. How filled sections are marked
and how scenarios are run as evals belong to the role generation procedure (planned).

## Checked by

`keellay check` (planned): front matter fields and values; all sections present and in order; every Owns row matches
the responsibility table; every project section has Evidence and Ask the owner; three to five scenarios, each with
WHEN and THEN.
