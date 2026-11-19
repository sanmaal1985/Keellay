"""Command-line entry point. Every command prints one JSON object to stdout, so agents can parse the result."""

import argparse
import json
import sys

from keellay import __version__
from keellay.method_files import method_dir

EXIT_OK = 0
EXIT_NOT_IMPLEMENTED = 3

# Commands that exist in the interface but are not built yet, with what each will do.
PLANNED = {
    "init": "Lay the method into a project: greenfield from scratch, brownfield after analysis and the owner's yes.",
    "check": "Run the project's checks (index co-change, doc links, code rules) for git hooks and CI.",
    "paths": "Resolve the project's artifact sections from its config.",
}


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def _info() -> int:
    path, bundled = method_dir()
    _emit({"command": "info", "status": "ok", "version": __version__, "method_dir": str(path),
           "method_bundled": bundled})
    return EXIT_OK


def _planned(name: str) -> int:
    _emit({"command": name, "status": "not_implemented", "message": PLANNED[name]})
    return EXIT_NOT_IMPLEMENTED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="keellay", description="Vendor-agnostic spec-driven development framework.")
    parser.add_argument("--version", action="version", version=f"keellay {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("info", help="Show the version and where the method files are.")
    for name, summary in PLANNED.items():
        commands.add_parser(name, help=f"(not implemented) {summary}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "info":
        return _info()
    return _planned(args.command)
