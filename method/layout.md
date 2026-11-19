# Artifact layout

A project that uses Keellay gets this layout by default:

```
AGENTS.md            constitution block (a managed section; the rest of the file is the project's)
docs/
  product/           PRD, ideas register, index
  specs/             living specs, one per capability, index
  changes/           open changes (plan, delta); closed ones move to changes/archive/
  adr/               append-only ADRs, index of what is in force
  lessons/           one file per lesson, active-lessons index
.keellay/
  config.toml        method version, level, section paths, adapters
  manifest.json      generated files with contract version and content hash
```

- **Any section can live elsewhere.** `.keellay/config.toml` maps a section to the project's own path, so an existing
  project keeps its documents where they are.
- **One resolver.** Tools, checks and generated role files find sections only through `keellay paths`; nothing
  hardcodes a path.
- **Brownfield.** `keellay init` detects existing sections and proposes, per section, to map it in place or move it
  to the default. Nothing is written before the owner's yes.
- **Role files** go where each adapter expects them; the manifest tracks them so upgrades can tell generated content
  from the project's edits.
