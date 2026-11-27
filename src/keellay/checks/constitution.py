"""The `constitution` check: the constitution is where the config says, has its four sections, and `AGENTS.md`
points to it.

A project without a constitution section (`constitution = false`) has nothing to check here, and one whose
constitution is in another repository has it checked there. Whether Rules holds the three rules every role follows is
left to review: their wording is the project's own.
"""

from keellay.checks import Finding
from keellay.checks.artifacts import section_path
from keellay.checks.links import links_in, target_path
from keellay.checks.markdown import section
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "constitution"
SECTIONS = ("Project", "Owner", "Read first", "Rules")
AGENTS = "AGENTS.md"
# A new project meets these findings first, so they say where the shape of both files is written down.
SHAPE = "the constitution format of the Keellay method (method/formats/constitution.md) shows its shape"


def check(project: Project, source: Source) -> list[Finding]:
    path = section_path(project, "constitution")
    if path is None:
        return []
    findings = []
    if not source.is_file(path):
        findings.append(Finding(CHECK, "error", path, None, f"the constitution is missing; the project's "
                                                            f"constitution section is {path}; {SHAPE}"))
    else:
        text = source.read(path)
        for title in SECTIONS:
            if section(text, title) is None:
                findings.append(Finding(CHECK, "error", path, None, f"the constitution has no `## {title}` section"))
    if not source.is_file(AGENTS):
        findings.append(Finding(CHECK, "error", AGENTS, None, f"{AGENTS} is missing; it carries the line that points "
                                                             f"agents to {path}; {SHAPE}"))
    elif not any(target_path(AGENTS, target) == path for _, target in links_in(source.read(AGENTS))):
        findings.append(Finding(CHECK, "error", AGENTS, None, f"{AGENTS} does not link to the constitution, {path}"))
    return findings
