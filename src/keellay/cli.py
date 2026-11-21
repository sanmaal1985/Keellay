"""Command-line entry point. Every command prints one JSON object to stdout, so agents can parse the result."""

import argparse
import json
import sys

from keellay import __version__
from keellay.checks import run_checks
from keellay.checks.source import StagedFiles, WorkingTree, is_git_repository
from keellay.method_files import method_dir
from keellay.paths import ConfigError, load_project

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CONFIG_ERROR = 2
EXIT_NOT_IMPLEMENTED = 3

# Commands that exist in the interface but are not built yet, with what each will do.
PLANNED = {
    "init": "Lay the method into a project: greenfield from scratch, brownfield after analysis and the owner's yes.",
}


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def _info() -> int:
    path, bundled = method_dir()
    _emit({"command": "info", "status": "ok", "version": __version__, "method_dir": str(path),
           "method_bundled": bundled})
    return EXIT_OK


def _paths() -> int:
    try:
        project = load_project()
    except ConfigError as error:
        _emit({"command": "paths", "status": "error", "message": str(error)})
        return EXIT_CONFIG_ERROR
    sections = {}
    for name, section in project.sections.items():
        resolved = section.resolve(project.root)
        sections[name] = {"path": section.path, "exists": resolved is not None and resolved.exists()}
    _emit({"command": "paths", "status": "ok", "root": project.root.as_posix(), "level": project.level,
           "sections": sections})
    return EXIT_OK


def _check(staged: bool) -> int:
    def error(message: str) -> int:
        _emit({"command": "check", "status": "error", "message": message})
        return EXIT_CONFIG_ERROR

    try:
        project = load_project()
        if staged and not is_git_repository(project.root):
            return error("--staged needs a git repository")
        source = StagedFiles(project.root) if staged else WorkingTree(project.root)
        findings = run_checks(project, source)
    except ConfigError as problem:
        return error(str(problem))
    failed = any(finding.severity == "error" for finding in findings)
    _emit({"command": "check", "status": "failed" if failed else "ok",
           "findings": [finding.to_json() for finding in findings]})
    return EXIT_FINDINGS if failed else EXIT_OK


def _planned(name: str) -> int:
    _emit({"command": name, "status": "not_implemented", "message": PLANNED[name]})
    return EXIT_NOT_IMPLEMENTED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="keellay", description="Vendor-agnostic spec-driven development framework.")
    parser.add_argument("--version", action="version", version=f"keellay {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("info", help="Show the version and where the method files are.")
    commands.add_parser("paths", help="Show the project's root, level and where each artifact section lives.")
    check = commands.add_parser("check", help="Check the project's artifacts against their formats.")
    check.add_argument("--staged", action="store_true", help="Check the files as staged in git, for a pre-commit hook.")
    for name, summary in PLANNED.items():
        commands.add_parser(name, help=f"(not implemented) {summary}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "info":
        return _info()
    if args.command == "paths":
        return _paths()
    if args.command == "check":
        return _check(args.staged)
    return _planned(args.command)
