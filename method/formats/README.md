# Artifact formats

One file per artifact type: what it is for, its required structure, an example and what checks it.

Common rules:

- **Metadata** is YAML front matter at the top of the file, flat `key: value` pairs. Agents already know it from
  `SKILL.md`; the CLI reads it with a YAML library.
- **Names** of files, folders, capabilities and topics are lowercase words joined by hyphens.
- **Every section with an index** changes its index in the same commit as the artifact.

| Format | Artifact | Status |
|---|---|---|
| [change.md](change.md) | Change: ID, folder, lifecycle, plan with role-tagged phases, index, branch name | draft |
| [spec.md](spec.md) | Living spec: requirements with IDs, EARS statements, scenarios | draft |
| [delta.md](delta.md) | Spec delta inside a change and how it is merged at close | draft |
| [bugfix.md](bugfix.md) | Fix path: current / expected / unchanged | draft |
| [adr.md](adr.md) | ADR: append-only decision, supersede rule, index of what is in force | draft |
| [lesson.md](lesson.md) | Lesson: occurrences, gap, rule, mechanism; repeats force a mechanism | draft |

Planned: PRD section, idea and the ideas register, constitution (`AGENTS.md` block).
