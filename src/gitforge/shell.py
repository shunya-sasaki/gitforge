"""Shell integration for the ``gf`` wrapper function.

The ``gitforge`` binary runs as a child process and therefore cannot
change the current directory of the parent shell. To support
``gf worktree switch``, a small shell function named ``gf`` wraps the
binary: for ``worktree switch`` it captures the path printed by
``gitforge`` and runs ``cd`` itself; every other invocation is passed
straight through.

Users install the function by evaluating the output of
``gitforge shell-init`` from their shell startup file, e.g.::

    eval "$(gitforge shell-init zsh)"

Each shell's snippet also aliases tab-completion so that ``gf`` is
completed exactly like ``gitforge`` (zsh and bash require
``gitforge --install-completion`` to have registered the completion
first; fish inherits it automatically through ``--wraps``).
"""

from typing import Annotated
from typing import Literal

import typer

Shell = Literal["zsh", "bash", "fish"]

_ZSH_INIT = """\
gf() {
    if [ "$1" = "worktree" ] && [ "$2" = "switch" ]; then
        local _gf_dir
        _gf_dir="$(command gitforge "$@")" || return
        if [ -n "$_gf_dir" ]; then
            builtin cd -- "$_gf_dir" || return
        fi
    else
        command gitforge "$@"
    fi
}

if (( $+functions[compdef] )); then
    compdef gf=gitforge 2>/dev/null
fi
"""

_BASH_INIT = """\
gf() {
    if [ "$1" = "worktree" ] && [ "$2" = "switch" ]; then
        local _gf_dir
        _gf_dir="$(command gitforge "$@")" || return
        if [ -n "$_gf_dir" ]; then
            builtin cd -- "$_gf_dir" || return
        fi
    else
        command gitforge "$@"
    fi
}

if complete -p gitforge &>/dev/null; then
    eval "$(complete -p gitforge | sed 's/ gitforge$/ gf/')"
fi
"""

_FISH_INIT = """\
function gf --wraps gitforge
    if test "$argv[1]" = "worktree"; and test "$argv[2]" = "switch"
        set -l _gf_dir (command gitforge $argv)
        or return
        if test -n "$_gf_dir"
            builtin cd $_gf_dir
        end
    else
        command gitforge $argv
    end
end
"""

_SHELL_INIT: dict[str, str] = {
    "zsh": _ZSH_INIT,
    "bash": _BASH_INIT,
    "fish": _FISH_INIT,
}


def shell_init(shell: Shell) -> str:
    """Return the ``gf`` wrapper function source for a shell.

    Args:
        shell: Target shell, one of ``zsh``, ``bash`` or ``fish``.

    Returns:
        The shell function definition to be evaluated by the shell.
    """
    return _SHELL_INIT[shell]


def shell_init_command(
    shell: Annotated[Shell, typer.Argument(help="Target shell.")] = "zsh",
) -> None:
    """Print the ``gf`` shell wrapper function.

    Add ``eval "$(gitforge shell-init zsh)"`` to your shell startup
    file to install the ``gf`` command, which lets
    ``gf worktree switch`` change the current directory.
    """
    print(shell_init(shell), end="")
