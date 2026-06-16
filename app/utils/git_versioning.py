from __future__ import annotations

import subprocess
from pathlib import Path


class GitVersioner:
    def __init__(self, repo_dir: Path | str = ".", remote: str = "origin", branch: str = "main") -> None:
        self.repo_dir = Path(repo_dir)
        self.remote = remote
        self.branch = branch

    def commit_and_push(self, message: str) -> bool:
        if not (self.repo_dir / ".git").exists():
            return False
        self._run(["git", "add", "data"])
        if not self._has_changes():
            return False
        self._run(["git", "commit", "-m", message])
        self._run(["git", "push", self.remote, self.branch])
        return True

    def _has_changes(self) -> bool:
        result = subprocess.run(
            ["git", "status", "--porcelain", "data"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())

    def _run(self, args: list[str]) -> None:
        subprocess.run(args, cwd=self.repo_dir, check=True)
