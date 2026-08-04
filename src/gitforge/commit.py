"""Record changes to the repository."""

import subprocess
from typing import Annotated

import typer

from gitforge.utils import TextSanitizer


class Commit:
    """Record changes to the repository."""

    def __init__(self, backend):
        """Initialize the Diff command wrapper."""
        self.backend = backend

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def commit(
        self,
        title: Annotated[str, typer.Option(help="Commit title")],
        body: Annotated[str | None, typer.Option(help="Commit body")] = None,
    ) -> None:
        """Record changes to the repository."""
        title = TextSanitizer.strip_ansi(title)
        if body is not None:
            body = TextSanitizer.strip_ansi(body)
            body = TextSanitizer.unescape_whitespace(body)
            cmds = ["git", "commit", "-m", f"{title}\n\n{body}"]
        else:
            cmds = ["git", "commit", "-m", f"{title}"]
        self._run(cmds)
