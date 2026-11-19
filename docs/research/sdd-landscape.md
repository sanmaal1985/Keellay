# SDD landscape — what Keellay takes from whom

Research note, 2026-11-20. Input for the Keellay design document. Each source was read from its repository
(or official docs for Kiro); claims below cite what the source itself says, not reviews of it.

| Source | Kind | Read at |
|---|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit) | CLI toolkit + agent skills | `61d3abb`, 2026-11-19 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | CLI + skills, delta specs | `0c737dc`, 2026-11-19 |
| [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) (v7 preview) | persona skills + workflows | `e435a22`, 2026-11-12 |
| [Agent OS](https://github.com/buildermethods/agent-os) (v3) | standards commands | `e892e61`, 2026-10-07 |
| [Keelson](https://github.com/fernandopetry/keelson) | Claude Code plugin | `dccffa6`, 2026-11-05 |
| [Kiro](https://kiro.dev/docs/) | IDE (closed), docs | docs read 2026-11-20 |
| [market-analyzer](https://github.com/IgorKonovalov/market-analyzer) | a project's own skill ecosystem | `6cc16da`, 2026-09-10 |
| Author's own Flutter project | a project's own process (roles, indexes, retro loop, hooks) | 2026-11-19 |

## One line each

- **Spec Kit** — a *process toolkit*: constitution → specify → clarify → plan → tasks → implement → converge,
  plus separate bug-fix and idea-assessment processes; everything is built from primitives (integrations,
  extensions, presets, workflows, bundles, catalogs). 40+ agent integrations (43 catalog entries, incl. `generic`).
- **OpenSpec** — *specs as current truth, changes as deltas*: `specs/` describes how the system works now,
  `changes/<name>/` holds proposal + design + tasks + a spec delta (ADDED / MODIFIED / REMOVED) merged on archive.
  Brownfield-first: you spec only what you change. 30+ tools; a machine-readable CLI contract; `stores` for
  cross-repo specs.
- **BMAD** — *personas and right-sized planning*: analyst, PM, PO, architect, UX, dev; planning depth chosen by how
  well-defined the intent is; epic retrospectives with sourced findings; a skill builder with evals; skills
  installed cross-vendor (`npx skills add`) and rendered per project by a script.
- **Agent OS** — *standards*: discover conventions from the codebase one area at a time (user confirms), index
  them, inject only the relevant ones into context; profiles with inheritance.
- **Keelson** — *engine + adapter*: a generic engine and a ~15-line per-project config; a ten-article Quality
  Charter with falsifiable rules; language profiles generated from the Charter when none is bundled; gates
  calibrated by complexity × risk; mutation gate; evals per agent; lessons one-per-file with provenance; postmortem
  that traces a gap to the mechanism that let it through. Claude Code only; 15 agents, 30+ commands.
- **Kiro** — *spec types and steering*: requirements (EARS) → design → tasks, design-first variant, bugfix specs
  (current / expected / unchanged behavior), tasks run in dependency waves; steering files with inclusion modes
  (`always`, `fileMatch`, `manual`, `auto`); reads `AGENTS.md`; 13 hook triggers incl. pre/post task.
- **market-analyzer** — *plans with owner tags and a close ceremony*: one plan per change with phases, each phase
  tagged with a closed-vocabulary owner skill and a done-when; implementers route by tag; review and close happen in
  a fresh architect session; living behavioral specs (borrowed from OpenSpec) with a CI freshness gate; skill evals;
  git-hook gates; explicit ADR when a process tool is evaluated and declined.
- **Author's project** — *product layer and learning loop*: PO role with PRD and an ideas register with statuses; a
  routine for analysing a new owner proposal; per-section indexes of "what is in force now"; retro → lessons with
  repeat counters → mechanism (hook, checklist, rule); mutation discipline (a mutant counts only when an assertion
  fails); device checks only with the owner's consent; "the owner decides".

## Comparison

| Dimension | Spec Kit | OpenSpec | BMAD | Agent OS | Keelson | Kiro | market-analyzer | Author's |
|---|---|---|---|---|---|---|---|---|
| Vendor reach | 40+ agents | 30+ tools | skills, cross-vendor installer | Claude, Cursor, others | Claude Code | Kiro only | Claude Code | Claude Code |
| Current-truth spec | constitution only; feature specs persist by team choice | **yes**, merged deltas | project context (minimal) | standards | charter + profiles | steering | **living specs**, gated | PRD + ADR index |
| Change unit | feature dir: spec / plan / tasks | change: proposal / design / tasks / delta | ticket / epic / story | shaped spec | SPEC / PLAN / TASK | requirements / design / tasks | plan with owner-tagged phases | task file |
| Requirement notation | prioritized user stories + independent tests | SHALL + WHEN/THEN | — | — | EARS + Given-When-Then | EARS | MUST + WHEN/THEN (specs) | checkbox AC |
| Decisions (ADR) | — | — | architecture doc | — | DEC entries in plan | design.md | **ADR, append-only** | **ADR + index of what is in force** |
| Product layer | idea assessment | explore | PM, PO, analyst | plan-product | brief, refine, PM, PO | — | — (architect interviews) | **PO, PRD, ideas register** |
| Brownfield | init in place, constitution from evidence, bounded first change | **spec only what you change** | project context from code | **discover standards** | init detects stack, asks only the rest | generate steering | — | manual migration |
| Roles / skills | commands | commands | personas | commands | agents | one agent | domain skills, owner vocabulary | four role skills |
| Skill generation | presets | profiles | rendered per project | profiles | **profiles generated from charter** | — | handmade + `project-context.md` | handmade |
| Gates | extension hooks | `validate` | review | — | **gates by complexity × risk**, many hooks | 13 hook triggers | **git hooks + CI**, spec freshness | commit hook, permissions |
| Independent review | `converge`, `analyze` | `verify` | code-review skill | — | independent reviewers | — | **fresh-session close** | same session |
| Learning loop | — | — | epic retrospective | — | **lessons audit, postmortem** | — | — | **retro → counters → mechanism** |
| Skill tests | self-test preset | — | **evals** | — | **evals per agent** | — | **evals per skill** | — |
| Ceremony scaling | processes chosen per need | default vs expanded profile | **planning path by intent** | — | auto vs guided | quick spec | plan vs direct fix | — |

## What Keellay takes

1. **Engine separate from project layer** (Keelson, Spec Kit). The method is versioned in one place; each project
   gets a small adapter and its own generated role files. This is the root cause of copied-skill drift, fixed.
2. **Generate project roles from the method** (Keelson profiles, BMAD rendering) — with a **contract per role**
   (required sections, rules, references) and **evals** (BMAD, Keelson, market-analyzer) that check the generated
   skill against the contract.
3. **Current truth vs change** (OpenSpec, market-analyzer): living specs describe what the system does now; a change
   carries a delta and is merged on close. Brownfield starts nearly empty and grows with each change.
4. **Requirement notation**: EARS for requirements (Kiro, Keelson), WHEN/THEN for scenarios (OpenSpec); the bugfix
   triple "current / expected / unchanged" (Kiro).
5. **Change unit = plan with owner-tagged phases and done-when** (market-analyzer), executed in dependency waves
   (Kiro, Keelson).
6. **ADRs append-only + an index of what is in force now** (market-analyzer + author's).
7. **Product layer**: PO, PRD, ideas register with statuses, owner-proposal routine (author's), idea assessment with
   go / clarify / stop (Spec Kit).
8. **Right-sized ceremony**: the path is chosen by how well-defined the intent is and by complexity × risk (BMAD,
   Keelson); a small fix needs no plan.
9. **Minimal project context** (BMAD's evidence): write down only what is expensive to derive from code — intent,
   rationale, what was rejected. Never restate structure the agent can read.
10. **Brownfield onboarding**: init in place on a reviewable baseline; detect, then ask only what cannot be inferred
    (Keelson); constitution only from evidence (Spec Kit); discover standards area by area with confirmation
    (Agent OS); first change bounded (Spec Kit, OpenSpec).
11. **Independent review**: review and close in a fresh context (market-analyzer); converge/verify against the spec
    (Spec Kit, OpenSpec).
12. **Learning loop to mechanism**: retro → lessons with repeat counters → hook / checklist / rule (author's); lessons
    one per file with provenance, postmortem tracing the gap to the mechanism (Keelson).
13. **Vendor-agnostic enforcement**: checks live in scripts run by git hooks and CI; agent hooks are thin adapters
    that call the same scripts (market-analyzer, author's). `AGENTS.md` as the shared entry point (Kiro, Keelson,
    BMAD).
14. **Machine-readable CLI output** for agents (OpenSpec's JSON contract).
15. **Record process decisions as ADRs**, including tools evaluated and declined (market-analyzer).

## What Keellay does not take

- Many agents and commands up front (Keelson, Spec Kit catalogs): ceremony grows with need, not on install.
- Autonomous end-to-end runs as the default (Keelson `auto`): the owner decides at the gates by default.
- A single 100+ KB index file (market-analyzer's plans README): indexes stay short and point to documents.

## Open questions for the design

1. **Artifact names and layout**: one tree (e.g. `keellay/` like `openspec/`) or the project's own `docs/` sections
   mapped by config?
2. **Specs**: OpenSpec-style deltas merged on close, or market-analyzer-style living specs reconciled by the
   architect — or deltas that the close ceremony merges into living specs?
3. **Role set**: fixed core (PO, architect, developer, manager) plus generated domain roles, or fully generated from
   the project analysis?
4. **Skill generation without a vendor skill-creator**: Keellay ships its own role-generation procedure and contract
   so any agent can run it; the Claude adapter may delegate to skill-creator.
5. **Strictness levels**: how many, and what each turns on (gates, independent review, living specs, retro).
6. **Distribution**: CLI (`keellay init`) in which runtime — Python (uv), Node (npx), or both via a thin launcher.
