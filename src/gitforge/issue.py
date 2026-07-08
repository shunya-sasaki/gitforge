"""Issue commands wrapper class."""

import subprocess
from importlib import resources
from pathlib import Path
from typing import Annotated

import pyperclip
import typer
from rich.console import Console
from rich.markdown import Markdown

from gitforge.utils import TextSanitizer


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
        title: Annotated[
            str, typer.Option("--title", "-t", help="Title for the issue")
        ],
        body: Annotated[
            str, typer.Option("--body", "-b", help="Body for the issue")
        ],
        label: Annotated[
            str | None,
            typer.Option("--label", "-l", help="Add labels by name"),
        ] = None,
    ):
        """Create a new issue."""
        title = TextSanitizer.strip_ansi(title)
        body = TextSanitizer.unescape_whitespace(body)
        body = TextSanitizer.strip_ansi(body)
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
        comments: Annotated[
            bool, typer.Option(help="View issue comments")
        ] = True,
    ):
        """View an issue."""
        match self.backend:
            case "GitHub":
                cmds = ["gh", "issue", "view", f"{number}"]
                proc = subprocess.run(cmds, capture_output=True)
                text = proc.stdout.decode()
                if comments:
                    cmds = ["gh", "issue", "view", f"{number}", "--comments"]
                proc = subprocess.run(cmds, capture_output=True)
                text += "\n" + proc.stdout.decode()
            case "Gitea":
                cmds = ["tea", "issue", f"{number}"]
                if comments:
                    cmds.append("--comments")
                proc = subprocess.run(cmds, capture_output=True)
                text = proc.stdout.decode()
        console = Console()
        markdown = Markdown(markup=text)
        console.print(markdown)
        pyperclip.copy(text)
        console.print("\nCopied contents to the clipboard.", style="bold blue")

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
            case _:
                pj_forge_dirpath = None
        content = None
        if pj_forge_dirpath is not None:
            pj_template_filepath = (
                pj_forge_dirpath / "ISSUE_TEMPLATE" / template_file
            )
            if pj_template_filepath.exists():
                content = pj_template_filepath.read_text()
        if content is None:
            template_resource = resources.files("gitforge").joinpath(
                "assets", "ISSUE_TEMPLATE", template_file
            )
            content = template_resource.read_text()
        print(content)
