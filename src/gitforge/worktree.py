"""Worktree commands wrapper class."""

import re
import subprocess
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from gitforge.utils import TextSanitizer

_BRANCH_BRACKET_PATTERN = re.compile(r"^\[(.*)\]$")


def _complete_branch(incomplete: str) -> list[str]:
    """Suggest existing worktree branches for shell completion.

    Runs standalone in the completion subprocess (Typer invokes the
    binary again with the completion environment), so it queries git
    directly instead of relying on any :class:`Worktree` instance.
    """
    proc = subprocess.run(["git", "worktree", "list"], capture_output=True)
    text = TextSanitizer.decode_safe(proc.stdout)
    branches = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        branch = _BRANCH_BRACKET_PATTERN.sub(r"\1", parts[2])
        if branch.startswith(incomplete):
            branches.append(branch)
    return branches


@dataclass
class _WorktreeItem:
    path: str
    branch: str
    commit_hash: str


class Worktree:
    """Worktree commands wrapper."""

    def __init__(self, backend):
        """Initlizer of Worktree."""
        self.backend = backend
        self.app = typer.Typer(help="Manage worktrees", no_args_is_help=True)
        self.app.command()(self.add)
        self.app.command()(self.remove)
        self.app.command()(self.list)
        self.app.command()(self.switch)

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

    def _worktree_list(self) -> list[_WorktreeItem]:
        proc = subprocess.run(["git", "worktree", "list"], capture_output=True)
        text = TextSanitizer.decode_safe(proc.stdout)
        lines = text.splitlines()
        items = []
        for line in lines:
            path, commit_hash, branch = line.split()
            branch = _BRANCH_BRACKET_PATTERN.sub(r"\1", branch)
            item = _WorktreeItem(
                path=path, commit_hash=commit_hash, branch=branch
            )
            items.append(item)
        return items

    def list(
        self,
        format: Annotated[
            Literal["plain", "json", "table"],
            typer.Option(help="Output format."),
        ] = "table",
    ):
        """List details of each worktree."""
        items = self._worktree_list()
        match format:
            case "plain":
                for item in items:
                    print(f"{item.path} {item.commit_hash} [{item.branch}]")
            case "json":
                list_dict = [asdict(item) for item in items]
                print(list_dict)
            case "table":
                table = Table(title="Worktree list")
                table.add_column("Worktree Path")
                table.add_column("Commit Hash")
                table.add_column("Branch")
                for item in items:
                    table.add_row(item.path, item.commit_hash, item.branch)
                console = Console()
                console.print(table)

    def switch(
        self,
        branch: Annotated[
            str,
            typer.Argument(
                help="Branch name",
                autocompletion=_complete_branch,
            ),
        ],
    ):
        """Print the worktree path for a branch.

        Intended to be run through the ``gf`` shell wrapper, which
        changes the current directory to the printed path. Errors go to
        stderr with a non-zero exit so the wrapper does not ``cd``.
        """
        items = self._worktree_list()
        path = None
        for item in items:
            if item.branch == branch:
                path = Path(item.path)
        if path is not None and not path.exists():
            typer.echo(f"Worktree does not exist: {path}", err=True)
            raise typer.Exit(code=1)
        print(path)

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
