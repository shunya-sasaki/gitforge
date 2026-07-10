"""Utilities for copying text to the clipboard.

Provides helpers that copy to the local clipboard, and that fall back to
the OSC52 terminal escape sequence when running on a remote host so the
text lands on the clipboard of the machine the user sits at.
"""

import base64
import os
import sys

import pyperclip


class ClipboardError(Exception):
    """Raised when text could not be copied to the clipboard."""


class Clipboard:
    """Copies text to the clipboard of the machine the user sits at.

    Over an SSH connection the local clipboard belongs to the remote
    host, so the text is handed to the terminal emulator with an OSC52
    escape sequence instead.
    """

    @classmethod
    def copy(cls, text: str) -> None:
        """Copy the given text to the clipboard.

        Uses an OSC52 escape sequence when ``SSH_CONNECTION`` is set in
        the environment, and the system clipboard otherwise.

        Args:
            text (str): The text to copy to the clipboard.

        Raises:
            ClipboardError: If the text could not be copied.

        """
        if os.environ.get("SSH_CONNECTION"):
            cls._copy_osc52(text)
            return
        try:
            pyperclip.copy(text)
        except pyperclip.PyperclipException as exc:
            raise ClipboardError(str(exc)) from exc

    @classmethod
    def _copy_osc52(cls, text: str) -> None:
        """Ask the terminal emulator to copy the text via OSC52.

        The text is base64-encoded and written to ``stdout`` inside an
        OSC52 escape sequence. When ``TMUX`` is set, the sequence is
        wrapped in a tmux passthrough so it reaches the outer terminal.

        Args:
            text (str): The text to copy to the clipboard.

        """
        payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
        sequence = f"\x1b]52;c;{payload}\x07"
        if os.environ.get("TMUX"):
            sequence = f"\x1bPtmux;\x1b{sequence}\x1b\\"
        sys.stdout.write(sequence)
        sys.stdout.flush()
