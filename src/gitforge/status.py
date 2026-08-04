"""Show the working tree status."""

import subprocess
from typing import Annotated

import typer
from rich.console import Console

from gitforge.utils import Clipboard
from gitforge.utils import ClipboardError
from gitforge.utils import TextSanitizer


class Status:
    """Show the working tree status."""

    #: Commands whose combined output makes up the status report.
    _COMMANDS = (
        ["git", "status", "--short"],
        ["git", "rev-parse", "HEAD"],
        ["git", "--no-pager", "log", "-1", "--oneline"],
    )

    def __init__(self, backend):
        """Initialize the Status command wrapper."""
        self.backend = backend
        self.console = Console()

    def _capture(self, cmds: list[str]) -> str:
        """Return the output of `cmds`, falling back to stderr on error."""
        proc = subprocess.run(cmds, capture_output=True)
        output = TextSanitizer.decode_safe(proc.stdout)
        if proc.returncode != 0:
            output += TextSanitizer.decode_safe(proc.stderr)
        return output

    def _print_safe(self, text: str) -> None:
        """Print text without raising on un-encodable characters.

        On Windows the console encoding (e.g. cp932) may not be able to
        represent every character in the status. Round-tripping through
        that encoding with ``errors="replace"`` guarantees ``print``
        never raises ``UnicodeEncodeError``.
        """
        print(TextSanitizer.encode_safe(text), end="")

    def _report(self) -> str:
        """Return the output of every command, one section each.

        Each section is headed by the command that produced it, so the
        report stays readable once it is pasted elsewhere.
        """
        sections = []
        for cmds in self._COMMANDS:
            # ``--no-pager`` is an implementation detail of capturing the
            # output, so it is left out of the displayed command line.
            label = " ".join(cmd for cmd in cmds if cmd != "--no-pager")
            # Only the trailing newline is trimmed; the leading space of
            # a ``git status --short`` line is part of its status code.
            body = self._capture(cmds).rstrip()
            sections.append(f"$ {label}\n{body}\n" if body else f"$ {label}\n")
        return "\n".join(sections)

    def status(
        self,
        copy: Annotated[
            bool,
            typer.Option(
                "--copy/--no-copy",
                "-c/-n",
                help="Copy the status to the system clipboard (default: on).",
            ),
        ] = True,
    ) -> None:
        """Show the working tree status.

        Prints the short working tree status, the `HEAD` commit hash and
        the one-line summary of the last commit, and copies the whole
        report to the system clipboard unless `--no-copy` is given.
        """
        report = self._report()
        self._print_safe(report)
        if not copy:
            return
        try:
            Clipboard.copy(report)
        except ClipboardError as exc:
            self.console.print(
                f"\nFailed to copy to the clipboard: {exc}",
                style="bold red",
            )
        else:
            self.console.print(
                "\nCopied the status to the clipboard.", style="bold green"
            )
