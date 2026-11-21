# Constitution

The constitution is what every agent reads before any work in the project: what the project is, who decides, what to
read first and the rules that hold everywhere. It keeps only what is expensive to derive from the code and the other
artifacts; everything else is linked, not repeated.

## File

`docs/constitution.md`, one per project. `AGENTS.md` stays the project's own file and carries one line that points
here:

```markdown
Before any work, read [docs/constitution.md](docs/constitution.md) and follow it.
```

The constitution:

```markdown
---
project: Family budget
updated: 2026-11-21
---

# Constitution: Family budget

## Project

A mobile app for a household to record spending and keep monthly limits. Product: [PRD](product/prd.md).
Stack: Flutter app, Supabase backend.

## Owner

The owner decides product and technology choices, approves every change and says yes before anything public:
releases, store listings, pushes to protected branches. Agents bring options with one recommendation and wait.

## Read first

1. Active lessons: [lessons/README.md](lessons/README.md)
2. Open changes: [changes/README.md](changes/README.md)
3. Decisions in force: [adr/README.md](adr/README.md)

## Rules

- Claims about files, configs, tools and prices are made after reading or checking them, never from memory.
- Code and commits are in English; the owner is answered in Russian.
- Stage files by name; LF line endings.
```

## Sections

- **Project:** what it is and its stack, in a few lines; the PRD has the rest.
- **Owner:** who decides what, and what needs the owner's yes. At level light this may be the only rule set.
- **Read first:** the indexes an agent reads at session start, in order. Active lessons come first.
- **Rules:** project-wide rules as short imperatives, each one an agent can follow and someone can check. A rule that
  comes from an ADR or a lesson links to it. Rules for one role belong in that role's contract, rules for one change
  in its plan.

## Rules

- **Minimal.** A line goes in only if an agent would otherwise get it wrong or spend long finding it out. Layout,
  commands and conventions visible in the repo are linked or left out.
- **The owner decides.** An edit to Owner or Rules needs the owner's yes; the commit updates `updated`.
- **A rule is the weakest mechanism.** A lesson whose mechanism is a constitution rule may still need a check or a
  hook; see [lesson.md](lesson.md).
- **Brownfield:** rules are taken from evidence in the project (existing agent files, CI, hooks, review comments) and
  proposed to the owner, not invented.

## Wiring

Agents that can import a file load the constitution directly, so it does not depend on the agent following the link
(Claude Code: `@docs/constitution.md` next to `@AGENTS.md` in `CLAUDE.md`). Wiring for each agent is set up by
`keellay init` (planned).

## Checked by

`keellay check` (planned): the file exists at the resolved path; front matter; the four sections are present; links
resolve; `AGENTS.md` links to the constitution.
