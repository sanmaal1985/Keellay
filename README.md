# Keellay

*Keel laying* is the ceremony that starts the building of a ship: the keel goes down first, and the whole hull is
built on it. Keellay lays that keel for software projects built with AI coding agents.

Keellay is a vendor-agnostic, spec-driven development (SDD) framework. It stores the **method** — roles, process,
artifact formats, gates and the rules that hold them together — and on `init` it derives a project's own setup from
it: role skills generated for the project's stack and needs, documents, indexes and checks.

- **Greenfield** — an empty project gets the method laid down from scratch.
- **Brownfield** — an existing project is analysed first (its structure, existing skills, agent instructions and
  documents), and Keellay proposes how to move it onto the method instead of overwriting what is there.

## Status

Research and design. Nothing to install yet.

## Principles (draft)

- **Method, not templates.** The framework is versioned in one place; each project gets a small adapter and its own
  generated roles, checked against a contract.
- **Vendor-agnostic.** Plain Markdown and scripts at the core; thin adapters per agent. Checks run in git hooks and
  CI, so they hold whatever agent wrote the change.
- **The owner decides.** Agents restate the request, show options with a recommendation, and act after a yes.
- **Mechanisms over memory.** A lesson that repeats becomes a hook, a checklist item or a rule.
- **Right-sized ceremony.** A small fix needs no plan; a large change gets specs, a plan and an independent review.

## License

[MIT](LICENSE)
