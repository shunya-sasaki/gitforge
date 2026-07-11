"""Utilities for sanitizing text.

Provides helpers for removing ANSI escape sequences and for unescaping
whitespace literals.
"""

import re
import sys

_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class TextSanitizer:
    """Cleans text of characters that are unwanted in output.

    Groups helpers for sanitizing text, such as removing ANSI escape
    sequences and unescaping whitespace literals.
    """

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        """Remove ANSI escape sequences from the given text.

        Args:
            text (str): The text that may contain ANSI escape sequences.

        Returns:
            str: The text with all ANSI escape sequences removed.

        """
        return _ANSI_ESCAPE_PATTERN.sub("", text)

    @classmethod
    def unescape_whitespace(cls, text: str) -> str:
        r"""Convert escaped whitespace literals into real characters.

        Turns the two-character sequences ``\n`` and ``\t`` into actual
        newline and tab characters.

        Args:
            text (str): The text containing escaped whitespace literals.

        Returns:
            str: The text with `\n` and `\t` literals unescaped.

        """
        out = text.replace("\\n", "\n")
        out = out.replace("\\t", "\t")
        return out

    @classmethod
    def decode_safe(cls, data: bytes, encoding: str = "utf-8") -> str:
        """Decode bytes into text without raising on invalid bytes.

        Replaces byte sequences that are not valid in the given
        encoding so that decoding subprocess output never raises
        ``UnicodeDecodeError``.

        Args:
            data (bytes): The bytes to decode.
            encoding (str): The encoding to decode with. Defaults to
                ``"utf-8"``.

        Returns:
            str: The decoded text with un-decodable bytes replaced.

        """
        return data.decode(encoding, errors="replace")

    @classmethod
    def encode_safe(cls, text: str) -> str:
        """Round-trip text through the console encoding safely.

        Replaces characters the current stdout encoding cannot
        represent so that printing never raises ``UnicodeError`` on
        consoles such as Windows cp932.

        Args:
            text (str): The text to make safe for the console.

        Returns:
            str: The text with un-encodable characters replaced.

        """
        encoding = sys.stdout.encoding or "utf-8"
        return text.encode(encoding, errors="replace").decode(encoding)
