"""Gitforge class that wraps coommand for git forges such as GitHub, Gitea."""

import json
import shutil
import subprocess
from typing import Literal

import typer

from gitforge.diff import Diff
from gitforge.issue import Issue
from gitforge.label import Label
from gitforge.models import ForgeUrl
from gitforge.pr import PullRequest
from gitforge.worktree import Worktree


class GitForge:
    """Wrapper for git forges CLI."""

    def __init__(self, remote_name: str = "origin"):
        """Initializer of GitForge."""
        self.is_git_available = self._is_installed("git")
        self.is_gh_available = self._is_installed("gh")
        self.is_tea_available = self._is_installed("tea")
        self.backend = self._detect_backend(remote_name)
        self.app = typer.Typer(no_args_is_help=True)
        diff = Diff(self.backend)
        issue = Issue(self.backend)
        label = Label(self.backend)
        pr = PullRequest(self.backend)
        worktree = Worktree(self.backend)
        self.app.command(name="diff")(diff.diff)
        self.app.add_typer(issue.app, name="issue")
        self.app.add_typer(label.app, name="label")
        self.app.add_typer(pr.app, name="pr")
        self.app.add_typer(worktree.app, name="worktree")

    def _is_installed(self, cmd: Literal["git", "gh", "tea"]) -> bool:
        ret = shutil.which(cmd=cmd)
        if ret is not None:
            return True
        else:
            return False

    def _detect_backend(
        self, remote_name: str = "origin", max_page: int = 255
    ) -> str | None:
        proc = subprocess.run(
            ["git", "remote", "get-url", remote_name], capture_output=True
        )
        remote_url = proc.stdout.decode("utf-8").strip()
        if "github.com" in remote_url:
            return "GitHub"
        if self.is_gh_available:
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
                    return "GitHub"
                elif remote_url == forge_url.url:
                    return "GitHub"
        if self.is_tea_available:
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
                        return "Gitea"
                    elif remote_url == forge_url.url:
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
    """
    forge = GitForge()
    forge.app()


if __name__ == "__main__":
    run()
