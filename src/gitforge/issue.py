"""Issue commands wrapper class."""

import subprocess
from pathlib import Path
from typing import Annotated

import typer


class Issue:
    """Issue commands wrapper."""

    def __init__(self, backend):
        """Initlizer of PullRequest."""
        self.backend = backend
        self.app = typer.Typer(help="Manage issues", no_args_is_help=True)
        self.app.command()(self.list)
        self.app.command()(self.create)
        self.app.command()(self.view)
        self.app.command()(self.template)

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def list(self):
        """List issue in a repository."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "issue", "list"]
            case "Gitea":
                cmds = ["tea", "issue", "list"]
        self._run(cmds)

    def create(
        self,
        title: Annotated[str, typer.Option(help="Title for the issue")],
        body: Annotated[str, typer.Option(help="Body for the issue")],
        label: Annotated[
            str | None, typer.Option(help="Add labels by name")
        ] = None,
    ):
        """Create a new issue."""
        body = body.replace("\\n", "\n").replace("\\t", "\t")
        match self.backend:
            case "GitHub":
                cmds = [
                    "gh",
                    "issue",
                    "create",
                    "--title",
                    title,
                    "--body",
                    body,
                ]
                if label is not None:
                    cmds.extend(["--label", label])

            case "Gitea":
                cmds = [
                    "tea",
                    "issue",
                    "create",
                    "--title",
                    title,
                    "--description",
                    body,
                ]
                if label is not None:
                    cmds.extend(["--labels", label])
        self._run(cmds)

    def view(
        self,
        number: Annotated[int, typer.Argument(help="Issue number")],
    ):
        """View an issue."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "issue", "view", f"{number}"]

            case "Gitea":
                cmds = ["tea", "issue", f"{number}"]
        self._run(cmds)

    def template(
        self,
        label: Annotated[
            str | None,
            typer.Option(help="Issue template to view by label name"),
        ] = None,
    ):
        """View a template for an issue."""
        match label:
            case "bug":
                template_file = "bug_report.md"
            case "enhancement":
                template_file = "feature_request.md"
            case _:
                template_file = "default.md"
        match self.backend:
            case "GitHub":
                pj_forge_dirpath = Path(".github")
            case "Gitea":
                pj_forge_dirpath = Path(".gitea")
        pj_template_filepath = (
            pj_forge_dirpath / "ISSUE_TEMPLATE" / template_file
        )
        if pj_template_filepath.exists():
            content = pj_template_filepath.read_text()
        else:
            template_filepath = (
                Path(__file__).parent
                / "assets"
                / "ISSUE_TEMPLATE"
                / template_file
            )
            content = template_filepath.read_text()
        print(content)
