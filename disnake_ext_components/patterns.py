import re
import typing as t

__all__: t.List[str] = [
    "STR",
    "INT",
    "STRICTINT",
    "FLOAT",
    "BOOL",
    "STRICTBOOL",
    "SNOWFLAKE",
]


STR: t.Pattern[str] = re.compile(r".*", re.DOTALL)
"""A pattern that matches anything. Supports multiline input."""

STRICTSTR: t.Pattern[str] = re.compile(r".*")
"""A pattern that matches anything. Does not support multiline input."""

INT: t.Pattern[str] = re.compile(r"[-+]?\d+")
"""A pattern that matches an integer number. Also matches a leading + or -.
If this is not desired, use `patterns.STRICTINT` instead.
"""

STRICTINT: t.Pattern[str] = re.compile(r"\d+")
"""A pattern that matches an integer number. Only matches if the entire string consists of digits."""

FLOAT: t.Pattern[str] = re.compile(r"[-+]?(?:\d*\.\d+|\d+)")
"""A pattern that matches a float. Also matches a leading + or -."""

BOOL: t.Pattern[str] = re.compile(r"true|false|t|f|yes|no|y|n|1|0|enable|disable|on|off", re.I)
"""A pattern that matches a bunch of different things that can be interpreted as a boolean.
If it is desired to only match "True" or "False", use `patterns.STRICTBOOL` instead.
"""

STRICTBOOL: t.Pattern[str] = re.compile(r"True|False")
"""A pattern that matches booleans "True" and "False"."""

SNOWFLAKE: t.Pattern[str] = re.compile(r"\d{15,20}")
"""A pattern that matches a Discord snowflake. This is a sequence of digits of length 15 - 20."""
