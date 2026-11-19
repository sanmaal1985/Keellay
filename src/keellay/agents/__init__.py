"""Per-agent wiring, one small module per agent.

Role skills are generated once, in the Agent Skills format (a folder with `SKILL.md`), and are the same for every
agent. Wiring only connects them to a given agent: it puts the skills where that agent looks for them, makes the agent
read `AGENTS.md`, and registers the agent's hooks so they call `keellay check`.

Planned: Claude Code, then other agents that read `AGENTS.md`.
"""
