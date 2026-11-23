# Role contracts

A contract defines what a role skill must contain — required sections, fixed rules, references — without saying
anything about a particular project. Every project gets the four core roles, generated from these contracts; more
roles are added only as instances of a core contract (for example `developer-flutter`) or from contracts in this
catalogue, with the owner's yes.

| Contract | Kind | Status |
|---|---|---|
| [product-owner](product-owner.md) | core | draft |
| [architect](architect.md) | core | draft |
| [developer](developer.md) | core | draft |
| [manager](manager.md) | core | draft |

## Responsibilities

Every artifact and every step of the process has one role that does it, "anyone" or "the phase's role" where any role
may; the owner holds the gates. The manager is a dispatcher: every hand-off between roles goes through it, it runs the
retro, and it does no product, design or code work itself. "Anyone" means any role or the owner.

| Artifact or step | Does it | Owner gate |
|---|---|---|
| New owner request: restate, route to product owner or architect | manager | owner's yes |
| Open questions to the owner: list at the end of the message, hold dependent work | manager | — |
| Hand-offs: route every row of the hand-off table | manager | — |
| Idea: write down as `new` | anyone | — |
| Idea: assess, set the verdict, keep the register | product-owner | `planned` / `declined`: owner |
| PRD: propose edits | product-owner | Purpose, Users, Non-goals, an area's Outcome: owner's yes |
| Change path (fix / change / feature); for a fix, its current / expected / unchanged lines | architect | owner confirms |
| Draft change: intent, scope, delta | architect | — |
| Design notes of a change (`design.md`) | architect | — |
| Phases: cut the change into phases with role, depends-on and done-when; questions to architect and product owner | developer | — |
| Review of the phases: system and code | architect | — |
| Review of the phases: business, for a change that serves a PRD area or an idea | product-owner | — |
| Plan with reviewed phases | — | `draft → approved`: owner |
| When a change is approved: the ideas it carries get its ID in `change`, the PRD areas it serves become `in-progress` | architect | — |
| `approved → in-progress`: start the first wave | manager | — |
| Branch and phase work (code, tests; steps inside a phase are optional) | the phase's role | — |
| Done-when: code and system, code review — every phase | architect | — |
| Done-when: business requirements — phases with a result a user can see, in a change that serves a PRD area or an idea | product-owner | — |
| `in-progress → review`, delta merge through the CLI (in the implementing pull request when plans and specs are in different repositories), fresh-context review | architect | — |
| `review → closed`, move to archive; ideas it carries → `done` | architect | owner's yes |
| Business check at review; PRD areas whose Outcome the change reached → `delivered` with the owner's yes to close | product-owner | — |
| Change → `dropped`; PRD area → `dropped` | — | owner |
| Fix: tests and the fix commit carrying the current / expected / unchanged lines | developer | — |
| Fix review at level strict, in a fresh context | architect | — |
| Re-review of fixes after the review at close that change a rule, a decision or more than wording, in a fresh context | architect | — |
| ADR: write, supersede, index | architect | `accepted`: owner |
| Lesson: record an occurrence when the process fails | anyone | — |
| Retro at review, before close; lesson counts, statuses (`mechanized`, `retired`) and index | manager | mechanism waiver: owner |
| Mechanism for a lesson repeated in a change, small (a rule in a role skill's project section, a checklist item, a constitution rule): made at review | architect | owner's yes |
| Mechanism for a repeated lesson, large: built in a change of its own | the phase's role | waiver for the change it repeated in: owner |
| Method change a lesson needs: recorded in the lesson as input for Keellay | architect | waiver for the change it repeated in: owner |
| New role or instance, strictness level change, through an ADR | architect | owner |
| Constitution: Project, Read first, Owner and Rules | architect | owner's yes |
| Project setup: hooks and CI checks, role skills and their evals | architect | owner's yes |

A phase is passed when every checker has passed it: the architect always, and the product owner for a phase with a
result a user can see, in a change that serves a PRD area or an idea.

The architect says what a change is (intent, scope, delta); the developer, who knows the code, cuts it into phases;
the architect and the product owner review the cut before the owner approves the plan.

## Hand-offs

Every hand-off between roles, and between a role and the owner, goes through the manager: the role hands the event to
the manager, and the manager hands it to the target. "To" names who acts next; "Answered by" names the hand-offs that
follow from it, "done" where nothing does. An owner's answer can always be "no, with what to change", which goes back
to the role that asked. Each contract's Hands off holds the rows where its role is in From or To, word for word, and
the manager's holds every row, so the routing is checked in one place.

| # | Event | From | To | Answered by |
|---|---|---|---|---|
| H1 | Request restated in the owner's words | manager | owner | H2, H3, H7, H16, H1 |
| H2 | Request about the product, confirmed: an idea, "is X worth building", users, goals, a PRD edit | owner | product-owner | H4, H33 |
| H3 | Request about the system, confirmed: a defect, a change, an ADR, a new role, instance or level, a constitution edit, project setup; or a large mechanism for a lesson (a hook or a check) | owner, architect | architect | H8, H33 |
| H4 | Verdict on an idea; a `clarify` verdict lists its questions | product-owner | owner | H5, H6, H7 |
| H5 | Answers to a `clarify` verdict, or a verdict sent back with what to change | owner | product-owner | H4 |
| H6 | Idea declined | owner | product-owner, to record `declined` and the Outcome | done |
| H7 | Idea planned | owner | product-owner, to record `planned`; architect, to propose the path | H8 |
| H8 | Path proposed; for a fix, its current / expected / unchanged lines | architect | owner | H9 |
| H9 | Path confirmed, sent back with what to change, or the work dropped | owner | architect | H10, H11, H8, H16 |
| H10 | Change drafted: intent, scope, delta | architect | developer, to cut into phases | H12 |
| H11 | Fix confirmed, with its current / expected / unchanged lines | architect | developer, to fix | H24 |
| H12 | Phases cut | developer | architect; product-owner, for a change that serves a PRD area or an idea | H13, H14 |
| H13 | Cut reviewed with findings | architect, product-owner | developer | H12 |
| H14 | Cut accepted by every reviewer: the plan | architect, product-owner | owner | H15 |
| H15 | Plan approved, sent back with what to change, or the change dropped | owner | architect: approved → updates the ideas it carries and the PRD areas it serves; sent back → takes the changes to the draft or, through the manager, to the developer | H17, H10, H12, H16 |
| H16 | Change or PRD area dropped | owner | architect, for a change: archives it and sets back to `planned` the PRD areas no other approved change serves; product-owner: records the change's ideas as the owner says, or marks the area `dropped` | done |
| H17 | Ideas and areas updated: start the first wave | architect | the roles of the first wave | H18 |
| H18 | Phase work done, its checks passing | the phase's role | architect; product-owner, for a phase with a result a user can see in a change that serves a PRD area or an idea; a checker whose own phase it is checks it in a fresh context | H19, H20, H26 |
| H19 | Phase passed by every checker: start the phases whose dependencies are now done | architect, product-owner | the roles of those phases | H18 |
| H20 | Phase failed, with the failing criteria | architect, product-owner | the phase's role | H18 |
| H21 | Question that needs another role, or a choice that is the owner's | any role | architect for the system; product-owner for the product; owner for a choice | H23, H22 |
| H22 | The approved plan needs a change: a phase, its scope or its done-when | any role | architect, who drafts the change to the plan; it goes through the cut, its review and the owner's approval again | H10, H12 |
| H23 | Question answered | architect, product-owner, owner | the role that asked | done |
| H24 | Fix committed | developer | architect, for its review at level strict; done at other levels | H25, done |
| H25 | Fix reviewed at level strict: passed, or findings | architect | manager; findings → developer | H24, done |
| H26 | Last phase passed: the change goes to review | architect, product-owner | architect, for the fresh-context review; product-owner, for a change that serves a PRD area or an idea, for the business check; manager, for the retro at level standard and up and, at every level, for lessons that repeated in the change | H27, H28, H30 |
| H27 | Review at close done: passed, or findings with the role that fixes each | architect | manager; findings → the role the findings name | H29, H35 |
| H28 | Business check done: passed, or findings with the role that fixes each | product-owner | manager; findings → the role the findings name | H29, H35 |
| H29 | Findings fixed | the role the findings name | architect, for a re-review in a fresh context when a fix changes a rule, a decision or more than wording; product-owner, for the business check again when the findings came from it; architect otherwise, listing the fixes in Close | H27, H28, H35 |
| H30 | Retro done (level standard and up) and lessons checked: a lesson that repeated in this change needs a mechanism | manager | architect, when a mechanism is needed | H31, H35 |
| H31 | Mechanism proposed for the repeated lesson: small (a rule in a role skill's project section, a checklist item, a constitution rule) or large (a hook, a check, or a change to the method, which becomes an idea for Keellay) | architect | owner: the yes for a small one, the waiver for a large one; a method change is recorded in the lesson as input for Keellay | H34 |
| H32 | Small mechanism made, with the owner's yes | architect | architect, for a re-review in a fresh context | H27 |
| H33 | The owner's yes needed: a PRD edit, an ADR to accept, a change or area to drop, a new role, instance or level, a constitution edit, project setup | product-owner, architect | owner | H34 |
| H34 | The owner's answer: yes, or no with what to change | owner | product-owner or architect, whichever asked | H33, H31, H32, H3, H16, H35, done |
| H35 | Review passed; business check passed where the change serves a PRD area or an idea; retro done at level standard and up; any repeated lesson's mechanism made or waived: ask to close | manager | owner | H36 |
| H36 | Yes to close, or sent back with what to change | owner | product-owner, when the change served PRD areas, to set `delivered` those whose Outcome it reached; then architect, to close and archive; sent back → the role the answer names | done, H29 |

## Contract file

`method/contracts/<role>.md`, one per role. A role the core and the catalogue do not cover is added to the catalogue
as a new contract, with the owner's yes; a project does not write contracts of its own.

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
| When active | the situations that call the role — a plan phase tagged with it, a kind of owner request, a status — in the words real requests use | the second part of `description` ("Use when: …"); not repeated in the body |
| Owns | the rows of the responsibility table that the role does, word for word, with their owner gates | fixed |
| Hands off | the rows of the hand-off table where the role is in From or To, word for word | fixed |
| Rules | numbered rules for this role, each marked `[check]` or `[instruction]` | fixed, word for word |
| Project sections | a table of the sections filled for each project (see below) | filled per project |
| References | the formats and procedures the role works with, each with when to read it | copied into the skill's `references/` |
| Scenarios | trigger queries and behaviour scenarios (see below) | not copied; they become the skill's evals |

How contracts are written:

- **Only what an agent would not know.** No general advice on design, coding or product work; a capable agent has
  it already. A contract holds the method's rules and points to the project's evidence.
- **Instructions, not a persona.** No "you are an architect"; a contract says what to do, when and with what.
- **One term per concept**, the terms of the formats: change, phase, delta, living spec, lesson.
- **Rules every role follows** — claims only after reading or checking, choices go to the owner as options with one
  recommendation, open questions are listed at the end of the message — are in the constitution (its format requires
  them), not repeated in contracts; every contract lists `constitution.md` in References. A contract's Rules hold only
  what is specific to the role. The one exception is the manager's rule on open questions: it restates the rule because
  it is the mechanism that holds it, together with the work that depends on an open question.
- **Each rule says how it holds.** `[check]`: a check in hooks or CI enforces it, and the rule names the check; a
  check not built yet is marked `planned`, and until it exists the rule holds only as an instruction. `[instruction]`:
  only the text holds it. A rule that keeps being broken moves from instruction to check through a lesson.
- **Nothing from one project.** A contract names no repository, CI job or file of a particular project, Keellay's own
  included.

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
| From the manager: draft the change for planned I0004, session expiry | yes |
| From the manager: is the export crash a fix or a change? | yes |
| From the manager: done-when check of phase 1 of C0007 | yes |
| Fix the typo on the login screen | no — manager |
| From the manager: assess I0004 | no — product-owner |
| From the manager: break C0007 into phases | no — developer |
```

Three to five of each. Near misses come from the other roles first: they are where selection goes wrong. A raw
owner request calls the manager; work the manager hands over is written "From the manager: …" and calls the role
that does it.

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

`<core role>-<qualifier>`: a role a project needs for its stack or its kind of work is an instance of a core role,
not a new free-form skill. Examples: `developer-flutter` and `developer-backend` in a repository with two stacks,
`developer-prompts` for a project whose product includes prompts for agents, `product-owner-marketing` for positioning
and the texts users read.

- **Setup analysis proposes the instances** from what it finds in the repository; each is added with the owner's yes.
- **An instance follows its core contract:** the same fixed parts, its own project sections, filled for its part of
  the repository.
- **The agent writes the instance's stack knowledge** — project sections and any references it needs, such as how
  this project tests a Flutter screen — from the project's evidence and the owner's answers. Keellay ships no stack
  reference packs.
- Plan phases may name an instance or the core role.

## Skill from a contract

The generated skill is a folder in the open Agent Skills format, named `<prefix>-<role>`; the prefix comes from
`.keellay/config.toml`, its default is the project name in lowercase words joined by hyphens, and it may be empty. An
instance is named `<prefix>-<core role>-<qualifier>`.

```
shop-architect/
  SKILL.md
  references/
    change.md           copied from method/formats/
    delta.md
```

```markdown
---
name: shop-architect
description: "Shop project role: Plans changes, ... Use when: The manager routes ...; A phase is finished ...."
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
- **`description`** opens with the project ("Shop project role: "), then Purpose and "Use when: " followed by the When
  active items joined by "; ", each without its final full stop, and one full stop at the end; word for word; at most
  1024 characters, written as a quoted string so colons and other punctuation stay valid YAML. Opening with the
  project makes an agent working in the project prefer the role over a general skill with similar triggers.
- **The body** starts with Owns: no title that repeats the name, no restated description. It stays under 500 lines;
  anything longer goes to `references/`.
- **References** are one level deep: each file sits in `references/`, together with the files those references link
  to, and the References section lists each with a line saying when to read it.

Plan phases keep naming the role (`Role: architect`); `metadata.keellay-contract` links the skill to its contract.

The CLI renders the skeleton — front matter, the fixed sections, the headings of the project sections, the copied
references — and records the contract, its version and each copied reference with its source and hash in
`.keellay/manifest.json`. The agent fills the project sections. On upgrade the CLI re-renders the fixed parts, copies
changed references again and keeps the filled sections. How filled sections are marked and how scenarios run as evals
belong to the role generation procedure (planned).

## Checked by

`keellay check` (planned).

- Contracts: front matter fields and values; all sections present and in order; every Owns row is a row of the
  responsibility table with that role, word for word, and every table row of that role is in its Owns (rows done by
  "anyone" or by the phase's role hold for every role and are not repeated in Owns); every rule marked `[check]` or
  `[instruction]`, every `[check]` rule names its check; every project section has Evidence and Ask the owner; Purpose
  and When active fit a description of at most 1024 characters with a project prefix of up to 30; three to five
  triggers of each kind; three to five behaviour scenarios, each with WHEN and THEN.
- Hand-offs: every row has an event, From and To; every "Answered by" names existing rows; each contract's Hands off
  is the rows where its role is in From or To (every row for the manager), word for word; every role that is in To
  has a When active item for the hand-offs addressed to it.
- Generated skills: front matter valid for the Agent Skills format; `name` with the configured prefix; `description`
  within 1024 characters and opening with the project; body under 500 lines; no fill markers left; no names from
  other projects; every file in `references/` listed in References and identical to its source; links resolve.
