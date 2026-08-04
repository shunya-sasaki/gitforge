"""Show changes between commits, commit and working tree, etc."""

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

import typer
from rich.console import Console

from gitforge.utils import Clipboard
from gitforge.utils import ClipboardError
from gitforge.utils import TextSanitizer


class Diff:
    """Show changes between commits, commit and working tree."""

    def __init__(self, backend):
        """Initialize the Diff command wrapper."""
        self.backend = backend
        self.console = Console()

    def _run(self, cmds: list[str], env: dict[str, str] | None = None) -> None:
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds, env=env)

    def _print_safe(self, text: str) -> None:
        """Print text without raising on un-encodable characters.

        On Windows the console encoding (e.g. cp932) may not be able to
        represent every character in the diff. Round-tripping through that
        encoding with ``errors="replace"`` guarantees ``print`` never
        raises ``UnicodeEncodeError``.
        """
        print(TextSanitizer.encode_safe(text), end="")

    @contextmanager
    def _temp_index(self) -> Iterator[dict[str, str]]:
        """Yield an environment whose git index includes untracked files.

        A copy of the repository index is made in a temporary file and
        ``git add --intent-to-add`` is run against that copy, so untracked
        files show up in a later ``git diff`` as new files. The real index
        is never modified, and the temporary copy is always removed.

        Yields:
            An environment mapping with ``GIT_INDEX_FILE`` pointing at the
            temporary index.
        """
        index_path = self._index_path()
        fd, temp_path = tempfile.mkstemp(prefix="gitforge-index-")
        os.close(fd)
        try:
            if index_path and os.path.exists(index_path):
                shutil.copyfile(index_path, temp_path)
            else:
                # No index yet (e.g. a repository without commits); let
                # git create the temporary one from scratch.
                os.unlink(temp_path)
            env = {**os.environ, "GIT_INDEX_FILE": temp_path}
            # ``:/`` matches the whole repository, so the result does not
            # depend on the directory the command was run from.
            subprocess.run(
                ["git", "add", "--intent-to-add", "--", ":/"],
                env=env,
                capture_output=True,
            )
            yield env
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _index_path(self) -> str:
        """Return the absolute path of the repository index file.

        The path is resolved with ``git rev-parse`` rather than assumed to
        be ``.git/index``, because linked worktrees keep their index
        elsewhere.
        """
        proc = subprocess.run(
            [
                "git",
                "rev-parse",
                "--path-format=absolute",
                "--git-path",
                "index",
            ],
            capture_output=True,
        )
        return TextSanitizer.decode_safe(proc.stdout).strip()

    def _show(
        self, cmds: list[str], copy: bool, env: dict[str, str] | None
    ) -> None:
        """Print the diff produced by `cmds`, optionally copying it."""
        if not copy:
            self._run(cmds, env=env)
            return
        proc = subprocess.run(cmds, capture_output=True, env=env)
        output = TextSanitizer.decode_safe(proc.stdout)
        self._print_safe(output)
        try:
            Clipboard.copy(output)
        except ClipboardError as exc:
            self.console.print(
                f"\nFailed to copy to the clipboard: {exc}",
                style="bold red",
            )
        else:
            self.console.print(
                "\nCopied the diff to the clipboard.", style="bold green"
            )

    def diff(
        self,
        branch: Annotated[
            str | None, typer.Argument(help="Branch name to compare against")
        ] = None,
        previous: Annotated[
            bool,
            typer.Option(
                "--previous/--no-previous",
                "-p/-P",
                help="Show the diff between the previous commit and HEAD.",
            ),
        ] = False,
        untracked: Annotated[
            bool,
            typer.Option(
                "--untracked/--no-untracked",
                "-u/-U",
                help="Include untracked files in the diff.",
            ),
        ] = False,
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
        the given branch and `HEAD`. With `--previous`, show the diff
        between the previous commit and `HEAD`.

        With `--untracked`, untracked files that are not ignored are
        included in the `HEAD` diff as new files. The option has no
        effect when comparing two commits, that is together with
        `branch` or `--previous`.
        """
        if previous:
            cmds = ["git", "--no-pager", "diff", "--no-color", "HEAD~..HEAD"]
        elif branch is None:
            cmds = ["git", "--no-pager", "diff", "--no-color", "HEAD"]
        else:
            cmds = [
                "git",
                "--no-pager",
                "diff",
                "--no-color",
                f"{branch}..HEAD",
            ]
        if untracked and not previous and branch is None:
            with self._temp_index() as env:
                self._show(cmds, copy, env)
        else:
            self._show(cmds, copy, None)
