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
| [prd.md](prd.md) | PRD: purpose, users, non-goals, areas with stable IDs that changes and ideas link to | draft |
| [idea.md](idea.md) | Idea: proposal, assessment with a verdict, owner's outcome; the ideas register | draft |

Planned: constitution.
