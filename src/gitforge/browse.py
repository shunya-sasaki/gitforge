"""Open repositories, issues, pull requests, and more in the browser."""

import subprocess


class Browse:
    """Open repositories, issues, pull requests, and more in the browser."""

    def __init__(self, backend):
        """Initialize the Browse command wrapper."""
        self.backend = backend

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def browse(self):
        """Open a repositoriy in the browser."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "browse"]
            case "Gitea":
                cmds = ["tea", "open"]
        self._run(cmds)
