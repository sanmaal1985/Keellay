# Artifact formats

One file per artifact type: what it is for, its required structure, an example and what checks it.

Common rules:

- **Metadata** is YAML front matter at the top of the file, flat `key: value` pairs. Agents already know it from
  `SKILL.md`; the CLI reads it with a YAML library.
- **Values are read as strings.** The CLI reads front matter without YAML type resolution, so `A0012` stays `A0012`
  and dates stay text; nothing needs quoting. A list, such as `supersedes: [A0004, A0007]`, is a list of strings.
- **Numbers** of changes, ideas, ADRs and lessons are the letter of their kind and four digits, with no separator:
  `C` for a change (`C0007`), `I` for an idea (`I0004`), `A` for an ADR (`A0012`), `L` for a lesson (`L0003`). Each
  kind counts on its own, from `0001`, and never reuses a number. The number is written in this form everywhere: file
  and folder names, front matter, links, branch names and prose (`see A0012`), so a reader never has to guess the kind.
- **Names** of files, folders, capabilities and topics are lowercase words joined by hyphens.
- **Every section with an index** changes its index in the same commit as the artifact.

| Format | Artifact | Status |
|---|---|---|
| [change.md](change.md) | Change: ID, folder, lifecycle, plan with role-tagged phases, index, branch name | draft |
| [spec.md](spec.md) | Living spec: requirements with IDs, EARS statements, scenarios | draft |
| [delta.md](delta.md) | Spec delta: where it lives, how and when it is merged into the living spec | draft |
| [bugfix.md](bugfix.md) | Fix path: current / expected / unchanged | draft |
| [adr.md](adr.md) | ADR: append-only decision, supersede rule, index of what is in force | draft |
| [lesson.md](lesson.md) | Lesson: occurrences, gap, rule, mechanism; repeats force a mechanism | draft |
| [prd.md](prd.md) | PRD: purpose, users, non-goals, areas with stable IDs that changes and ideas link to | draft |
| [idea.md](idea.md) | Idea: proposal, assessment with a verdict, owner's outcome; the ideas register | draft |
| [constitution.md](constitution.md) | Constitution: project, owner, what to read first, project-wide rules; linked from `AGENTS.md` | draft |
