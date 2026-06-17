"""Worktree commands wrapper class."""

import subprocess
from pathlib import Path
from typing import Annotated

import typer


class Worktree:
    """Worktree commands wrapper."""

    def __init__(self, backend):
        """Initlizer of Worktree."""
        self.backend = backend
        self.app = typer.Typer(help="Manage worktrees", no_args_is_help=True)
        self.app.command()(self.add)
        self.app.command()(self.remove)

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def add(self, branch: Annotated[str, typer.Argument(help="Branch name")]):
        """Create a worktree for a branch under."""
        path = self._worktree_path(branch)
        if path.exists():
            print(f"Worktree already exists: {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        cmds = ["git", "worktree", "add", str(path)]
        if self._branch_exists(branch):
            cmds.append(branch)
        else:
            cmds.extend(["-b", branch])
        self._run(cmds)
        print(path)

    def remove(
        self, branch: Annotated[str, typer.Argument(help="Branch name")]
    ):
        """Remove the worktree for a branch."""
        path = self._worktree_path(branch)
        if not path.exists():
            print(f"Worktree does not exist: {path}")
            return
        self._run(["git", "worktree", "remove", str(path)])

    def _repo_name(self, remote_name: str = "origin") -> str:
        """Get the repository name from the remote URL."""
        proc = subprocess.run(
            ["git", "remote", "get-url", remote_name], capture_output=True
        )
        remote_url = proc.stdout.decode("utf-8").strip().rstrip("/")
        # Handle both "git@host:owner/repo.git" and "https://host/owner/repo.git".
        name = remote_url.rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def _worktree_path(self, branch_name: str) -> Path:
        """Build the worktree path as ~/.tmp/<repo-name>_<branch-name>."""
        safe_branch = branch_name.replace("/", "-")
        dir_name = f"{self._repo_name()}_{safe_branch}"
        return Path.home() / ".tmp" / dir_name

    def _branch_exists(self, branch_name: str) -> bool:
        """Check whether a local branch already exists."""
        proc = subprocess.run(
            [
                "git",
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/heads/{branch_name}",
            ]
        )
        return proc.returncode == 0
