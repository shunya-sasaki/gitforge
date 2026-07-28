"""Gitforge class that wraps coommand for git forges such as GitHub, Gitea."""

import io
import json
import shutil
import subprocess
import sys
from typing import Literal

import typer
from rich.console import Console

from gitforge.browse import Browse
from gitforge.commit import Commit
from gitforge.diff import Diff
from gitforge.issue import Issue
from gitforge.label import Label
from gitforge.models import ForgeUrl
from gitforge.pr import PullRequest
from gitforge.shell import shell_init_command
from gitforge.worktree import Worktree


class GitForge:
    """Wrapper for git forges CLI."""

    def __init__(self, remote_name: str = "origin"):
        """Initializer of GitForge."""
        self.console = Console()
        self.remote_name = remote_name
        self.is_git_available = self._is_installed("git")
        self.is_gh_available = False
        self.is_tea_available = False
        self.backend: str | None = None
        self.app = typer.Typer(no_args_is_help=True)
        self._browse = Browse(None)
        self._commit = Commit(None)
        self._diff = Diff(None)
        self._issue = Issue(None)
        self._label = Label(None)
        self._pr = PullRequest(None)
        self._worktree = Worktree(None)
        self._backend_commands = (
            self._browse,
            self._commit,
            self._diff,
            self._issue,
            self._label,
            self._pr,
            self._worktree,
        )
        self.app.callback()(self._setup)
        self.app.command(name="shell-init")(shell_init_command)
        self.app.command(name="diff")(self._diff.diff)
        self.app.command(name="commit")(self._commit.commit)
        self.app.command(name="browse")(self._browse.browse)
        self.app.add_typer(self._issue.app, name="issue")
        self.app.add_typer(self._label.app, name="label")
        self.app.add_typer(self._pr.app, name="pr")
        self.app.add_typer(self._worktree.app, name="worktree")

    def _setup(self, ctx: typer.Context) -> None:
        """Detect the repository and backend before running a command.

        Runs as the Typer group callback ahead of each subcommand.
        ``shell-init`` is skipped so it works outside a repository and
        without the cost of querying the forge; every other subcommand
        requires a git worktree and a resolved backend.
        """
        if ctx.invoked_subcommand == "shell-init":
            return
        if not self._is_inside_work_tree():
            self.console.print(
                "Not inside a git worktree. "
                + "Run gitforge from within a git repository.",
                style="red",
            )
            raise typer.Exit()
        self.is_gh_available = self._is_installed("gh")
        self.is_tea_available = self._is_installed("tea")
        self.backend = self._detect_backend(self.remote_name)
        for command in self._backend_commands:
            command.backend = self.backend

    def _is_inside_work_tree(self) -> bool:
        cmds = ["git", "rev-parse", "--is-inside-work-tree"]
        proc = subprocess.run(cmds, capture_output=True)
        if proc.returncode == 0:
            return True
        else:
            return False

    def _is_installed(self, cmd: Literal["git", "gh", "tea"]) -> bool:
        ret = shutil.which(cmd=cmd)
        if ret is not None:
            return True
        else:
            return False

    def _is_backend_github(self, remote_url: str, limit: int = 255) -> bool:
        cmds = ["gh", "auth", "status"]
        proc = subprocess.run(cmds, capture_output=True)
        if proc.returncode == 1:
            return False
        proc = subprocess.run(
            [
                "gh",
                "repo",
                "list",
                "--json",
                "sshUrl,url",
                "--limit",
                f"{limit}",
            ],
            capture_output=True,
        )
        output = proc.stdout.decode("utf-8")
        output_json = json.loads(output)
        gh_urls = [
            ForgeUrl(sshUrl=item["sshUrl"], url=item["url"])
            for item in output_json
        ]
        for forge_url in gh_urls:
            if remote_url == forge_url.sshUrl:
                return True
            elif remote_url == forge_url.url:
                return True
        return False

    def _is_backend_gitea(self, remote_url: str, max_page: int = 255) -> bool:
        for i_page in range(max_page):
            proc = subprocess.run(
                [
                    "tea",
                    "repo",
                    "list",
                    "-f",
                    "ssh,url",
                    "-o",
                    "json",
                    "--page",
                    f"{i_page + 1}",
                ],
                capture_output=True,
            )
            output = proc.stdout.decode("utf-8")
            output_json = json.loads(output)
            if len(output_json) == 0:
                break
            tea_urls = [
                ForgeUrl(sshUrl=item["ssh"], url=item["url"])
                for item in output_json
            ]
            for forge_url in tea_urls:
                if remote_url == forge_url.sshUrl:
                    return True
                elif remote_url == forge_url.url:
                    return True
        return False

    def _detect_backend(
        self,
        remote_name: str = "origin",
        max_page: int = 255,
        limit: int = 255,
    ) -> str | None:
        proc = subprocess.run(
            ["git", "remote", "get-url", remote_name], capture_output=True
        )
        remote_url = proc.stdout.decode("utf-8").strip()
        if "github.com" in remote_url:
            return "GitHub"
        if self.is_gh_available:
            if self._is_backend_github(remote_url, limit=limit):
                return "GitHub"
        if self.is_tea_available:
            if self._is_backend_gitea(remote_url, max_page=max_page):
                return "Gitea"
        return None

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)


def run():
    """Run the gitforge command-line interface.

    Builds a :class:`GitForge` instance, which detects the available
    backend and registers the subcommands, then dispatches the Typer
    application to handle the invoked command.

    Reconfigures stdout/stderr to UTF-8 first so output does not raise
    ``UnicodeEncodeError`` when the streams are piped to a legacy code
    page (e.g. Windows cp932 under OpenCode).
    """
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")
    forge = GitForge()
    forge.app()


if __name__ == "__main__":
    run()
