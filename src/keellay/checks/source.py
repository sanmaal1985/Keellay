"""Where checks read files from: the working tree, or the git index for a pre-commit hook.

Paths are relative to the project root and use `/`. A hook checks what is being committed, so an unfinished file
that another session has not staged does not stop the commit when parallel sessions share one checkout.
"""

import os
import subprocess
from pathlib import Path, PurePosixPath


class Source:
    """The project's files as one snapshot: what exists and what it contains."""

    def files(self) -> list[str]:
        raise NotImplementedError

    def read(self, path: str) -> str:
        raise NotImplementedError

    def is_file(self, path: str) -> bool:
        return path in self._file_set()

    def is_dir(self, path: str) -> bool:
        prefix = path.rstrip("/") + "/"
        return path in ("", ".") or any(name.startswith(prefix) for name in self._file_set())

    def exists(self, path: str) -> bool:
        return self.is_file(path) or self.is_dir(path)

    def files_under(self, path: str) -> list[str]:
        """The file itself, or every file inside the folder."""
        if self.is_file(path):
            return [path]
        prefix = path.rstrip("/") + "/"
        return sorted(name for name in self._file_set() if name.startswith(prefix))

    def _file_set(self) -> set[str]:
        cache = getattr(self, "_cached_files", None)
        if cache is None:
            cache = set(self.files())
            self._cached_files = cache
        return cache


# Folders that are never project content.
_SKIPPED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}


class WorkingTree(Source):
    def __init__(self, root: Path):
        self.root = root

    def files(self) -> list[str]:
        found = []
        for folder, dirs, names in os.walk(self.root):
            dirs[:] = [name for name in dirs if name not in _SKIPPED_DIRS]
            relative = Path(folder).relative_to(self.root)
            found += [PurePosixPath(*relative.parts, name).as_posix() for name in names]
        return found

    def read(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8")


class StagedFiles(Source):
    """The files in the git index, read in one `git cat-file --batch` call."""

    def __init__(self, root: Path):
        self.root = root
        self._contents: dict[str, str] | None = None

    def files(self) -> list[str]:
        out = self._git("ls-files", "-z", "--cached")
        return [name for name in out.decode("utf-8").split("\0") if name]

    def read(self, path: str) -> str:
        if self._contents is None:
            self._contents = self._read_all()
        return self._contents[path]

    def _read_all(self) -> dict[str, str]:
        names = [name for name in self.files() if name.endswith(".md")]
        request = "".join(f":{name}\n" for name in names).encode("utf-8")
        out = self._git("cat-file", "--batch", stdin=request)
        contents, offset = {}, 0
        for name in names:
            header_end = out.index(b"\n", offset)
            header = out[offset:header_end].split()
            size = int(header[2])
            start = header_end + 1
            contents[name] = out[start:start + size].decode("utf-8", errors="replace")
            offset = start + size + 1  # the blob is followed by a newline
        return contents

    def _git(self, *args: str, stdin: bytes | None = None) -> bytes:
        result = subprocess.run(["git", *args], cwd=self.root, input=stdin, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"git {args[0]} failed: {result.stderr.decode('utf-8', errors='replace').strip()}")
        return result.stdout


def is_git_repository(root: Path) -> bool:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True,
                            check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"
