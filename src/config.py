#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   config.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/10/18 17:00:00 by enchueco              #+#    #+#          #
#   Updated: 2026/10/18 17:00:00 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

"""Load the JSON (with comments) configuration file of the game."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any


class ConfigError(Exception):
    """Raised when the configuration file cannot be used at all."""


MIN_LEVELS = 10
DEFAULT_LEVEL: dict[str, int] = {"width": 18, "height": 18}

# key: (default, min, max)
NUMBERS: dict[str, tuple[float, float, float]] = {
    "lives": (3, 1, 99),
    "points_per_pacgum": (10, 0, 100000),
    "points_per_super_pacgum": (50, 0, 100000),
    "points_per_ghost": (200, 0, 100000),
    "seed": (42, 0, 2 ** 31 - 1),
    "level_max_time": (90, 10, 3600),
    "pacman_speed": (10, 1, 100),
    "ghost_speed": (7.5, 1, 100),
    "frightened_time": (7, 1, 60),
    "ghost_respawn_time": (5, 1, 60),
}
INT_KEYS = ("lives", "points_per_pacgum", "points_per_super_pacgum",
            "points_per_ghost", "seed", "level_max_time")
LEVEL_LIMITS: dict[str, tuple[int, int]] = {"width": (8, 30),
                                            "height": (8, 30)}
DEFAULT_HIGHSCORE = "scores_board.json"


def warn(msg: str) -> None:
    """Print a configuration warning on stderr.

    Args:
        msg: Message to print.
    """
    print(f"[config] warning: {msg}", file=sys.stderr)


def strip_comments(text: str) -> str:
    """Remove the comments of a JSON text.

    Lines starting with ``#`` or ``//`` and ``/* ... */`` blocks are removed.

    Args:
        text: Raw file content.

    Returns:
        The text without comments.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        start = line.lstrip()
        if start.startswith("#") or start.startswith("//"):
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def _number(data: dict[str, Any], key: str) -> float:
    """Read a number from the config, clamped, with a default.

    Args:
        data: Parsed config.
        key: Key to read (must be in ``NUMBERS``).

    Returns:
        The value to use.
    """
    default, low, high = NUMBERS[key]
    if key not in data:
        warn(f"'{key}' is missing, default {default} used")
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        warn(f"'{key}' must be a number, default {default} used")
        return default
    if key in INT_KEYS and not float(value).is_integer():
        warn(f"'{key}' must be an integer, rounded")
        value = round(value)
    if value < low or value > high:
        clamped = min(max(value, low), high)
        warn(f"'{key}' must be between {low} and {high}, {clamped} used")
        value = clamped
    return int(value) if key in INT_KEYS else float(value)


def _levels(data: dict[str, Any]) -> list[dict[str, int]]:
    """Read and check the list of levels.

    Args:
        data: Parsed config.

    Returns:
        At least ``MIN_LEVELS`` levels with valid ``width``/``height``
        (and an optional ``seed``).
    """
    raw = data.get("levels", data.get("level"))
    levels: list[dict[str, int]] = []
    if raw is None:
        warn("'levels' is missing, default levels used")
        raw = []
    elif not isinstance(raw, list):
        warn("'levels' must be an array, default levels used")
        raw = []
    for i, lvl in enumerate(raw):
        if not isinstance(lvl, dict):
            warn(f"level {i + 1} must be an object, default size used")
            lvl = {}
        clean: dict[str, int] = {}
        for key, (low, high) in LEVEL_LIMITS.items():
            value = lvl.get(key, DEFAULT_LEVEL[key])
            if isinstance(value, bool) or not isinstance(value, int):
                warn(f"level {i + 1}: '{key}' must be an integer, "
                     f"default {DEFAULT_LEVEL[key]} used")
                value = DEFAULT_LEVEL[key]
            if not low <= value <= high:
                clamped = min(max(value, low), high)
                warn(f"level {i + 1}: '{key}' must be between {low} and "
                     f"{high}, {clamped} used")
                value = clamped
            clean[key] = value
        seed = lvl.get("seed")
        if seed is not None:
            if (isinstance(seed, int) and not isinstance(seed, bool)
                    and seed >= 0):
                clean["seed"] = seed
            else:
                warn(f"level {i + 1}: 'seed' must be a positive integer, "
                     "ignored")
        levels.append(clean)
    if len(levels) < MIN_LEVELS:
        if raw:
            warn(f"the game needs at least {MIN_LEVELS} levels, "
                 "default levels added")
        while len(levels) < MIN_LEVELS:
            levels.append(dict(DEFAULT_LEVEL))
    return levels


def load_config(path: str) -> dict[str, Any]:
    """Read, parse and validate the configuration file.

    Missing or invalid values are replaced by safe defaults (with a
    warning), unknown keys are ignored.

    Args:
        path: Path of the JSON configuration file.

    Returns:
        A dict holding every config key with a valid value.

    Raises:
        ConfigError: If the file cannot be read or is not a JSON object.
    """
    if not path.lower().endswith(".json"):
        raise ConfigError(f"'{path}': the configuration must be a .json file")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise ConfigError(f"'{path}': file not found")
    except IsADirectoryError:
        raise ConfigError(f"'{path}': is a directory")
    except PermissionError:
        raise ConfigError(f"'{path}': permission denied")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"'{path}': cannot be read ({exc})")
    try:
        data = json.loads(strip_comments(text))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"'{path}': invalid JSON line {exc.lineno} "
                          f"column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        raise ConfigError(f"'{path}': the root must be a JSON object")

    conf: dict[str, Any] = {}
    for key in NUMBERS:
        conf[key] = _number(data, key)
    conf["levels"] = _levels(data)

    name = data.get("highscore_filename", DEFAULT_HIGHSCORE)
    if not isinstance(name, str) or not name.strip():
        warn("'highscore_filename' must be a non empty string, "
             f"default '{DEFAULT_HIGHSCORE}' used")
        name = DEFAULT_HIGHSCORE
    if not os.path.isabs(name):
        name = os.path.join(os.path.dirname(os.path.abspath(path)), name)
    conf["highscore_filename"] = name
    return conf
