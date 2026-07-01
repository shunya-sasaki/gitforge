"""Show changes between commits, commit and working tree, etc."""

import subprocess
import sys
from typing import Annotated

import pyperclip
import typer


class Diff:
    """Show changes between commits, commit and working tree."""

    def __init__(self, backend):
        """Initialize the Diff command wrapper."""
        self.backend = backend

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def _print_safe(self, text: str) -> None:
        """Print text without raising on un-encodable characters.

        On Windows the console encoding (e.g. cp932) may not be able to
        represent every character in the diff. Round-tripping through that
        encoding with ``errors="replace"`` guarantees ``print`` never
        raises ``UnicodeEncodeError``.
        """
        encoding = sys.stdout.encoding or "utf-8"
        safe = text.encode(encoding, errors="replace").decode(encoding)
        print(safe, end="")

    def diff(
        self,
        branch: Annotated[
            str | None, typer.Argument(help="Branch name to compare against")
        ] = None,
        copy: Annotated[
            bool,
            typer.Option(
                "--copy/--no-copy",
                "-c/-n",
                help="Copy the diff to the system clipboard (default: on).",
            ),
        ] = True,
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
        if copy:
            proc = subprocess.run(cmds, capture_output=True)
            output = proc.stdout.decode("utf-8", errors="replace")
            self._print_safe(output)
            try:
                pyperclip.copy(output)
            except pyperclip.PyperclipException as exc:
                print(f"\nFailed to copy to the clipboard: {exc}")
            else:
                print("\nCopied the diff to the clipboard.")
        else:
            self._run(cmds)
