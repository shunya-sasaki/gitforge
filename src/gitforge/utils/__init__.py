"""Shared utility helpers for gitforge.

Exposes helpers for copying text to the clipboard, such as
:class:`Clipboard`, and for sanitizing text, such as
:class:`TextSanitizer`.
"""

from gitforge.utils.clipboard import Clipboard
from gitforge.utils.clipboard import ClipboardError
from gitforge.utils.sanitizer import TextSanitizer

__all__ = ["Clipboard", "ClipboardError", "TextSanitizer"]
