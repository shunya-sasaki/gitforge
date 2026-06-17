"""gitforge: a unified CLI wrapper for git forges such as GitHub and Gitea.

This package exposes the :func:`run` entry point, which detects the
available backend and dispatches the Typer application that provides the
``pr``, ``issue``, ``label`` and ``worktree`` subcommands.
"""

from gitforge.gitforge import run

__all__ = ["run"]
