"""Pull request commands wrapper class."""

import subprocess
from importlib import resources
from pathlib import Path
from typing import Annotated

import typer


class PullRequest:
    """Pull request command wrapper."""

    def __init__(self, backend):
        """Initlizer of PullRequest."""
        self.backend = backend
        self.app = typer.Typer(
            help="Manage pull requests", no_args_is_help=True
        )
        self.app.command()(self.list)
        self.app.command()(self.create)
        self.app.command()(self.view)
        self.app.command()(self.merge)
        self.app.command()(self.template)

    def _run(self, cmds: list[str]):
        """Run a forge command, streaming its output to the terminal."""
        subprocess.run(cmds)

    def list(self):
        """List pull requests in a repository."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "pr", "list"]
            case "Gitea":
                cmds = ["tea", "pr", "list"]
        self._run(cmds)

    def create(
        self,
        title: Annotated[
            str, typer.Option("--title", "-t", help="Supply a title")
        ],
        body: Annotated[
            str, typer.Option("--body", "-b", help="Supply a body")
        ],
        base: Annotated[
            str, typer.Option("--base", "-B", help="Target branch")
        ] = "main",
        label: Annotated[
            str | None,
            typer.Option("--label", "-l", help="Add label by name"),
        ] = None,
    ):
        """Create a new pull request."""
        body = body.replace("\\n", "\n").replace("\\t", "\t")
        match self.backend:
            case "GitHub":
                cmds = [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    title,
                    "--body",
                    body,
                ]
                if base is not None:
                    cmds.extend(["--base", base])
                if label is not None:
                    cmds.extend(["--label", label])

            case "Gitea":
                cmds = [
                    "tea",
                    "pr",
                    "create",
                    "--title",
                    title,
                    "--description",
                    body,
                ]
                if base is not None:
                    cmds.extend(["--base", base])
                if label is not None:
                    cmds.extend(["--labels", label])
        self._run(cmds)

    def view(
        self,
        number: Annotated[int, typer.Argument(help="Pull request number")],
    ):
        """View a pull request."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "pr", "view", f"{number}"]

            case "Gitea":
                cmds = ["tea", "pr", f"{number}"]
        self._run(cmds)

    def merge(
        self,
        number: Annotated[int, typer.Argument(help="Pull request number")],
    ):
        """Merge a pull request."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "pr", "merge", f"{number}"]

            case "Gitea":
                cmds = ["tea", "pr", "merge", f"{number}"]
        self._run(cmds)

    def template(
        self,
        create: Annotated[
            bool,
            typer.Option(
                is_flag=True, help="Create a pull request template file"
            ),
        ] = False,
    ):
        """View a template."""
        template_file = "pull_request_template.md"
        match self.backend:
            case "GitHub":
                pj_forge_dirpath = Path(".github")
                pj_template_filepath = pj_forge_dirpath / template_file
                content = pj_template_filepath.read_text()
            case "Gitea":
                pj_forge_dirpath = Path(".gitea")
                pj_template_filepath = pj_forge_dirpath / template_file
                content = pj_template_filepath.read_text()
            case _:
                content = None
        if content is None:
            template_resource = resources.files("gitforge").joinpath(
                "assets", template_file
            )
            content = template_resource.read_text()
        if create and not pj_template_filepath.exists():
            print("Create a template")

        print(content)
