"""Label commands wrapper class."""

import subprocess

import typer


class Label:
    """Label command wrapper."""

    def __init__(self, backend):
        """Initlizer of PullRequest."""
        self.backend = backend
        self.app = typer.Typer(help="Manage labels", no_args_is_help=True)
        self.app.command()(self.list)

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def list(self):
        """List labels in a repository."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "label", "list"]
            case "Gitea":
                cmds = ["tea", "label", "list"]
        self._run(cmds)
