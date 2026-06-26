"""Show changes between commits, commit and working tree, etc."""

import subprocess
from typing import Annotated

import typer


class Diff:
    """Show changes between commits, commit and working tree."""

    def __init__(self, backend):
        """Initialize the Diff command wrapper."""
        self.backend = backend

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def diff(
        self,
        branch: Annotated[
            str | None, typer.Argument(help="Branch name to compare against")
        ] = None,
    ):
        """Show changes between commits, commit and working tree.

        Without `branch`, show the diff of the current uncommitted
        changes against `HEAD`. With `branch`, show the diff between
        the given branch and `HEAD`.
        """
        if branch is None:
            cmds = ["git", "--no-pager", "diff", "--no-color", "HEAD"]
        else:
            cmds = [
                "git",
                "--no-pager",
                "diff",
                "--no-color",
                f"{branch}..HEAD",
            ]
        self._run(cmds)
