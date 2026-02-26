"""Generate the expected help-output strings used in test_cli.py.

Run this script after changing a docstring or CLI parameter. Only snippets
whose output differs from the current constants in test_cli.py are printed,
so you can copy-paste just the changed values back into that file.

Usage:
    just generate-help-strings
"""

import sys
from io import StringIO

from rich.console import Console

from seedcase_flower.cli import app
from tests.test_cli import _BUILD_HELP_PAGE, _HELP_PAGE


def _capture_help(args: list[str]) -> str:
    """Return the help text produced by *args* as a plain string."""
    console = Console(
        width=90,
        force_terminal=True,
        highlight=False,
        color_system=None,
        legacy_windows=False,
    )

    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        try:
            app(args, console=console)
        except SystemExit:
            pass
        return sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout


def _as_constant_snippet(name: str, text: str) -> str:
    """Return a copy-pasteable constant assignment for *text*."""
    lines = text.splitlines()
    indented_body = "\n".join(f"    {line}" if line else "" for line in lines)
    return f'{name} = dedent(\n    """\\\n{indented_body}\n    """  # noqa\n)'


if __name__ == "__main__":
    checks = [
        ("_HELP_PAGE", ["--help"], _HELP_PAGE),
        ("_BUILD_HELP_PAGE", ["build", "--help"], _BUILD_HELP_PAGE),
    ]
    changed = [
        (name, args) for name, args, current in checks if _capture_help(args) != current
    ]

    if not changed:
        print("No changes detected. All help-output constants are up to date.")
    else:
        print()
        print("Review that the output below looks as expected.")
        print("Then, copy and paste it into tests/test_cli.py,")
        print("replacing the variable(s) with the same name.")
        for name, args in changed:
            print()
            print()
            print()
            print(_as_constant_snippet(name, _capture_help(args)))
