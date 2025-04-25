from typing import Any, Literal

from click import style

COLORS = Literal["cyan", "blue", "green", "yellow", "red", "bright_red"]


def log_param(
    param: str,
    value: Any,
    param_color: COLORS = "cyan",
    value_color: COLORS = "blue",
    separator: str = ":",
) -> str:
    """Returns the colorized parameter and value for logging purposes."""
    return "%s%s %s" % (
        style(param, fg=param_color),
        separator,
        style(value, fg=value_color),
    )
