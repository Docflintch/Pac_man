#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   tools.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/07/31 06:24:00 by enchueco              #+#    #+#          #
#   Updated: 2026/07/31 06:24:00 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

"""Helpers: sprites, responsive grid, highscores and maze loading."""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict, deque
from typing import Any

from mazegenerator import MazeGenerator

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame  # noqa: E402

MAX_SCORES = 10
MAX_NAME_LEN = 10


def decoder_tailles(paires: list[Any], nb_p_ligne: list[int]) -> list[Any]:
    """Expand the compressed ``[value, nb_lines, ...]`` sprite description.

    Args:
        paires: Pairs ``value, nb``. A value can be a list of pairs
            ``value, nb_sprite`` describing one line sprite by sprite.
        nb_p_ligne: Number of sprites on each line of the sheet.

    Returns:
        One value per sprite of the sheet.
    """
    tailles: list[Any] = []
    ligne_actuelle = 0
    for i in range(0, len(paires), 2):
        cp = paires[i]
        nb = paires[i + 1]
        if isinstance(cp, list):
            for y in range(0, len(cp), 2):
                cp_l = cp[y]
                nb_l = cp[y + 1]
                tailles += [cp_l] * (nb_l)
        else:
            tailles += [cp] * sum(nb_p_ligne[ligne_actuelle:
                                             ligne_actuelle + nb])
        ligne_actuelle += nb
    return tailles


def type_row(y: int) -> str:
    """Give the kind of sprites stored on a line of the sprite sheet.

    Args:
        y: Line of the sheet.

    Returns:
        ``"ghost"``, ``"Scared"``, ``"PAC"``, ``"obj"`` or ``"wall_roof"``.
    """
    if y >= 0 and y < 4:
        return "ghost"
    elif y == 4:
        return "Scared"
    elif y == 5:
        return "PAC"
    elif y == 6:
        return "obj"
    else:
        return "wall_roof"


def init_pygame() -> pygame.Surface:
    """
    this function initializes pygame and returns the screen surface

    returns:
        the screen surface
    """
    pygame.init()
    sc = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("PAC_MAN")
    return sc


def responcive_pos(sc: pygame.Surface,
                   ptc: tuple[float, float]) -> tuple[float, float]:
    """
    this function return the pose compared with the screen size

    args:
        sc: the screen surface
        ptc: the percentage of the width and of the height

    returns:
        a tuple containing the new x and y position
    """
    x_ptc, y_ptc = ptc
    h = sc.get_height()
    w = sc.get_width()
    x = w * (x_ptc / 100)
    y = h * (y_ptc / 100)
    return (x, y)


def responsive_size(sc: pygame.Surface, ptc_sc: float,
                    sp: pygame.Surface) -> tuple[int, int]:
    """
    this function return the size compared with the screen size

    args:
        sc: the screen surface
        ptc_sc: the percentage of the screen width
        sp: the sprite to resize

    returns:
        a tuple containing the new width and height
    """
    sp_w, sp_h = sp.get_size()
    w = round(sc.get_width() * ptc_sc / 100)
    ratio = w / sp_w
    h = round(sp_h * ratio)
    return (w, h)


def load_image(path: str) -> pygame.Surface:
    """Load an image, or quit cleanly if it is missing.

    Args:
        path: Path of the image.

    Returns:
        The loaded surface.
    """
    try:
        return pygame.image.load(path).convert_alpha()
    except (FileNotFoundError, pygame.error):
        print(f"Error: {path} files not find", file=sys.stderr)
        pygame.quit()
        sys.exit(1)


def restor_sp() -> dict[str, Any]:
    """Cut the sprite sheet into named animations.

    Returns:
        ``{"ghost": [4 dicts], "PAC": dict, "obj": dict, "wall_roof": list}``
    """
    sheet = load_image("sprite/sprite.png")
    ln_sp = ["down", 1, "up", 1, "left", 1, "right", 1, "scared", 1,
             ["moov", 3, "dead", 10], 1,
             ["Super_Pacgum", 1, "Pacgum", 1, "_", 4, "cheat", 2,
              "life", 1, "life_dead", 1, "cheat", 1], 1,
             ["wall", 1, "roof", 1, "angel", 4], 1]
    value_s: list[Any] = [[8, 8, 8, 8, 4, 13, 11, 3],
                          [
                              (103, 103), 6,
                              [(55, 55), 2, (82, 81), 4, (38, 84), 1,
                               (96, 91), 4], 1,
                              (35, 35), 1,
                          ]]
    # value_s[0] == nb sprite par ligne | value_s[1] == size of sprite
    sprite_size = decoder_tailles(value_s[1], value_s[0])
    sp_name = decoder_tailles(ln_sp, value_s[0])
    all_sp: dict[str, Any] = {
        "ghost": [defaultdict(list) for _ in range(4)],
        "PAC": defaultdict(list),
        "obj": defaultdict(list),
        "wall_roof": [],
    }
    idx = 0
    for y, nb_col in enumerate(value_s[0]):
        t_row = type_row(y)
        for x in range(nb_col):
            n_sp = sp_name[idx]
            width, height = sprite_size[idx]
            rect = pygame.Rect(x * 103, y * 103, width, height)
            scrap = sheet.subsurface(rect).copy()
            idx += 1

            if t_row == "ghost":
                all_sp["ghost"][x // 2][n_sp].append(scrap)
            elif t_row == "Scared":
                for i in range(4):
                    all_sp["ghost"][i][n_sp].append(scrap)
            elif t_row == "wall_roof":
                all_sp[t_row].append(scrap)
            else:
                all_sp[t_row][n_sp].append(scrap)

    all_sp["PAC"]["dead"] = all_sp["PAC"]["dead"][::-1]
    return all_sp


def grid(screen: pygame.Surface, cols: float,
         rows: float) -> tuple[float, float, float]:
    """Compute the biggest square grid that fits in the window.

    Args:
        screen: Window surface.
        cols: Number of columns of the grid.
        rows: Number of rows of the grid.

    Returns:
        ``(offset_x, offset_y, step)`` in pixels.
    """
    w, h = screen.get_size()

    step = min(w / cols, h / rows)

    grid_w, grid_h = step * cols, step * rows
    ox = (w - grid_w) / 2
    oy = (h - grid_h) / 2

    return ox, oy, step


def reachable_cells(grid_map: list[list[int]],
                    start: tuple[int, int]) -> set[tuple[int, int]]:
    """List the tiles that can be reached from ``start`` (BFS).

    Args:
        grid_map: Tile map.
        start: ``(x, y)`` start tile.

    Returns:
        Every reachable ``(x, y)`` tile.
    """
    seen, queue = {start}, deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in seen and \
                    0 <= ny < len(grid_map) and \
                    0 <= nx < len(grid_map[ny]) and \
                    grid_map[ny][nx] <= 0:
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


def valid_name(name: str) -> bool:
    """Tell whether a player name can be saved.

    Args:
        name: Player name.

    Returns:
        ``True`` for 1 to 10 alphanumeric characters or spaces (not only
        spaces).
    """
    return (0 < len(name) <= MAX_NAME_LEN and bool(name.strip())
            and all(c.isalnum() or c == " " for c in name))


def load_scores(filename: str) -> list[dict[str, Any]]:
    """Load the highscores, ignoring every invalid entry.

    Args:
        filename: Path of the JSON highscore file.

    Returns:
        At most 10 ``{"name": str, "score": int}``, best score first.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Warning: highscores '{filename}' unreadable ({exc})",
              file=sys.stderr)
        return []
    if not isinstance(data, list):
        return []
    scores: list[dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name, score = entry.get("name"), entry.get("score")
        if not isinstance(name, str) or not valid_name(name):
            continue
        if isinstance(score, bool) or not isinstance(score, int) \
                or score < 0:
            continue
        scores.append({"name": name, "score": score})
    scores.sort(key=lambda s: s["score"], reverse=True)
    return scores[:MAX_SCORES]


def save_score(filename: str, name: str,
               score: int) -> list[dict[str, Any]]:
    """Add a score to the highscores and keep the 10 best.

    Args:
        filename: Path of the JSON highscore file.
        name: Player name (checked with ``valid_name``).
        score: Score (negative values are saved as 0).

    Returns:
        The new highscore list.
    """
    scores = load_scores(filename)
    if not valid_name(name):
        return scores
    scores.append({"name": name, "score": max(0, int(score))})
    scores.sort(key=lambda s: s["score"], reverse=True)
    scores = scores[:MAX_SCORES]
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=4)
    except OSError as exc:
        print(f"Warning: highscores not saved ({exc})", file=sys.stderr)
    return scores


CORRIDOR = 0
WALL = 1
ROOF = 2
CORNER_TOP_LEFT = 3
CORNER_BOTTOM_LEFT = 4
CORNER_BOTTOM_RIGHT = 5
CORNER_TOP_RIGHT = 6
PAC_START = -1
GHOST_STARTS = (-2, -3, -4, -5)

_NORTH, _EAST, _SOUTH, _WEST = 1, 2, 4, 8
_FULL_CELL = 15


class MazeError(Exception):
    """Raised when a maze cannot be generated or converted."""


def _validate(maze: list[list[int]]) -> tuple[int, int]:
    """Check the shape and content of a cell maze.

    Args:
        maze: Cell maze as produced by ``MazeGenerator.maze``.

    Returns:
        The ``(width, height)`` of the maze, in cells.

    Raises:
        MazeError: If the maze is empty, ragged or has invalid cell values.
    """
    if not maze or not maze[0]:
        raise MazeError("the maze is empty")
    width = len(maze[0])
    for row in maze:
        if len(row) != width:
            raise MazeError("the maze rows have different lengths")
        for cell in row:
            if not isinstance(cell, int) or not 0 <= cell <= _FULL_CELL:
                raise MazeError(f"invalid maze cell value: {cell!r}")
    return width, len(maze)


def _is_closed(maze: list[list[int]], x: int, y: int) -> bool:
    """Tell whether a cell exists and is a closed "42" cell."""
    return (0 <= y < len(maze) and 0 <= x < len(maze[0])
            and maze[y][x] == _FULL_CELL)


def _build_solid_map(maze: list[list[int]], width: int,
                     height: int) -> list[list[bool]]:
    """Upscale the cell maze to a boolean map telling which tiles are wall.

    Closed cells keep only the outline of their zone: their centre and the
    walls between two closed cells stay empty.
    """
    solid = [[False] * (2 * width + 1) for _ in range(2 * height + 1)]
    sides = ((_NORTH, 0, -1), (_EAST, 1, 0), (_SOUTH, 0, 1), (_WEST, -1, 0))
    for y in range(height):
        for x in range(width):
            cell = maze[y][x]
            tx, ty = 2 * x + 1, 2 * y + 1
            for bit, dx, dy in sides:
                if not cell & bit:
                    continue
                if cell == _FULL_CELL and _is_closed(maze, x + dx, y + dy):
                    continue  # inside the zone: no wall
                solid[ty + dy][tx + dx] = True
    # Pillars are walls only when a wall touches them (unchanged).
    for ty in range(0, 2 * height + 1, 2):
        for tx in range(0, 2 * width + 1, 2):
            solid[ty][tx] = (_is_solid(solid, tx, ty - 1)
                             or _is_solid(solid, tx + 1, ty)
                             or _is_solid(solid, tx, ty + 1)
                             or _is_solid(solid, tx - 1, ty))
    return solid


def _is_solid(solid: list[list[bool]], x: int, y: int) -> bool:
    """Tell whether a tile is a wall (out-of-map tiles are not).

    Args:
        solid: Boolean wall map.
        x: Tile column.
        y: Tile row.

    Returns:
        ``True`` if ``(x, y)`` is inside the map and is a wall.
    """
    return 0 <= y < len(solid) and 0 <= x < len(solid[0]) and solid[y][x]


def _wall_kind(solid: list[list[bool]], x: int, y: int) -> int:
    """Pick the sprite id of a wall tile from its neighbours.

    Args:
        solid: Boolean wall map.
        x: Tile column.
        y: Tile row.

    Returns:
        One of ``WALL`` (vertical), ``ROOF`` (horizontal) or a corner id.
    """
    up = _is_solid(solid, x, y - 1)
    down = _is_solid(solid, x, y + 1)
    left = _is_solid(solid, x - 1, y)
    right = _is_solid(solid, x + 1, y)
    if down and right and not (up or left):
        return CORNER_TOP_LEFT
    if up and right and not (down or left):
        return CORNER_BOTTOM_LEFT
    if up and left and not (down or right):
        return CORNER_BOTTOM_RIGHT
    if down and left and not (up or right):
        return CORNER_TOP_RIGHT
    # Straight pieces, ends and junctions: horizontal wall = roof, vertical
    # wall = wall. A junction goes to the side holding most of its branches
    # (a cross counts as vertical).
    if (left + right) > (up + down):
        return ROOF
    return WALL


def _nearest_free_cell(maze: list[list[int]], target: tuple[float, float],
                       used: set[tuple[int, int]]) -> tuple[int, int]:
    """Find the open cell closest to a target point.

    Args:
        maze: Validated cell maze.
        target: Wanted ``(x, y)`` position, in cells (may be fractional).
        used: Cells that are already taken.

    Returns:
        The ``(x, y)`` cell, never a closed "42" cell and never in ``used``.

    Raises:
        MazeError: If every cell is closed or taken.
    """
    best: tuple[float, int, int] | None = None
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == _FULL_CELL or (x, y) in used:
                continue
            dist = (x - target[0]) ** 2 + (y - target[1]) ** 2
            if best is None or (dist, y, x) < best:
                best = (dist, y, x)
    if best is None:
        raise MazeError("the maze has no free cell for a start position")
    return best[2], best[1]


def convert_maze(maze: list[list[int]]) -> list[list[int]]:
    """Convert a ``MazeGenerator`` cell maze into the game's tile map.

    Args:
        maze: ``MazeGenerator.maze`` (4-bit wall masks, row by row).

    Returns:
        The tile map, see the module docstring for the meaning of values.

    Raises:
        MazeError: If the maze is invalid or too small to hold the 5 starts.
    """
    width, height = _validate(maze)
    solid = _build_solid_map(maze, width, height)
    grid = [[_wall_kind(solid, x, y) if solid[y][x] else CORRIDOR
             for x in range(len(solid[0]))] for y in range(len(solid))]

    used: set[tuple[int, int]] = set()
    pac = _nearest_free_cell(maze, ((width - 1) / 2, (height - 1) / 2), used)
    used.add(pac)
    grid[2 * pac[1] + 1][2 * pac[0] + 1] = PAC_START
    corners = [(0, 0), (width - 1, 0), (0, height - 1),
               (width - 1, height - 1)]
    for value, corner in zip(GHOST_STARTS, corners):
        gx, gy = _nearest_free_cell(maze, (corner[0], corner[1]), used)
        used.add((gx, gy))
        grid[2 * gy + 1][2 * gx + 1] = value
    return grid


def generate_level(width: int, height: int, seed: int = 0,
                   perfect: bool = False) -> list[list[int]]:
    """Generate a maze with the A-Maze-ing package and convert it.

    Args:
        width: Maze width, in cells.
        height: Maze height, in cells.
        seed: Generator seed (``0`` means a random maze).
        perfect: ``False`` gives Pac-Man compatible mazes (no dead ends).

    Returns:
        The tile map, see :func:`convert_maze`.

    Raises:
        MazeError: If the generator or the conversion fails.
    """
    try:
        generator = MazeGenerator(size=(width, height), perfect=perfect,
                                  seed=seed)
        maze = generator.maze
    except Exception as exc:  # the package is a black box: never crash
        raise MazeError(f"maze generator failed: {exc}") from exc
    return convert_maze(maze)
