#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   ghost_ai.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/10/16 16:34:42 by enchueco              #+#    #+#          #
#   Updated: 2026/10/16 16:34:42 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

DIRECTIONS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE: dict[str, str] = {
    "up": "down", "down": "up", "left": "right", "right": "left",
}
UNREACHABLE = -1


@dataclass(frozen=True)
class GhostProfile:
    """Parameters that make a ghost behave differently from the others.

    Attributes:
        detection_range: Walking distance (in tiles) under which the ghost
            sees Pac-Man and chases him. One maze cell is 2 tiles.
        randomness: Probability (0..1) of a random move at a junction
            instead of the chase/flee move.
        keep_straight: Probability (0..1) of going straight on, while
            wandering, when that is possible.
    """

    detection_range: int
    randomness: float
    keep_straight: float


# One profile per ghost, in the order of the start values -2, -3, -4, -5.
GHOST_PROFILES: tuple[GhostProfile, ...] = (
    GhostProfile(detection_range=24, randomness=0.05, keep_straight=0.80),
    GhostProfile(detection_range=16, randomness=0.15, keep_straight=0.70),
    GhostProfile(detection_range=10, randomness=0.25, keep_straight=0.60),
    GhostProfile(detection_range=6, randomness=0.35, keep_straight=0.50),
)


def is_walkable(grid: list[list[int]], x: int, y: int) -> bool:
    """Tell whether a tile can be walked on.

    Args:
        grid: Tile map.
        x: Tile column.
        y: Tile row.

    Returns:
        ``True`` if ``(x, y)`` is inside the map and is not a wall.
    """
    return 0 <= y < len(grid) and 0 <= x < len(grid[y]) and grid[y][x] <= 0


def distance_field(grid: list[list[int]],
                   origin: tuple[int, int]) -> list[list[int]]:
    """Compute the walking distance from ``origin`` to every tile (BFS).

    Compute it once per Pac-Man move and share it between all the ghosts.

    Args:
        grid: Tile map.
        origin: ``(x, y)`` tile to measure from, usually Pac-Man's.

    Returns:
        A map of the same size as ``grid`` holding the number of steps from
        ``origin``, or ``UNREACHABLE`` (-1) for walls and cut-off tiles.
    """
    dist = [[UNREACHABLE] * len(row) for row in grid]
    ox, oy = origin
    if not is_walkable(grid, ox, oy):
        return dist
    dist[oy][ox] = 0
    queue: deque[tuple[int, int]] = deque([(ox, oy)])
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRECTIONS.values():
            nx, ny = x + dx, y + dy
            if is_walkable(grid, nx, ny) and dist[ny][nx] == UNREACHABLE:
                dist[ny][nx] = dist[y][x] + 1
                queue.append((nx, ny))
    return dist


class GhostBrain:
    """Decision maker of one ghost (same algorithm for every ghost)."""

    def __init__(self, profile: GhostProfile,
                 rng: random.Random | None = None) -> None:
        """Create a brain.

        Args:
            profile: Parameters of this ghost.
            rng: Random generator, handy to make tests reproducible.
        """
        self.profile = profile
        self.rng = rng if rng is not None else random.Random()
        self.direction = "up"

    def decide(self, grid: list[list[int]], pos: tuple[int, int],
               pac_dist: list[list[int]], edible: bool = False) -> str:
        """Choose the direction to take from the tile the ghost is on.

        Args:
            grid: Tile map.
            pos: ``(x, y)`` tile of the ghost.
            pac_dist: Result of :func:`distance_field` from Pac-Man's tile.
            edible: ``True`` while the ghosts can be eaten.

        Returns:
            ``"up"``, ``"down"``, ``"left"`` or ``"right"``. The current
            direction is kept if the ghost is walled in.
        """
        x, y = pos
        options = [name for name, (dx, dy) in DIRECTIONS.items()
                   if is_walkable(grid, x + dx, y + dy)]
        if not options:
            return self.direction
        ahead = [d for d in options if d != OPPOSITE[self.direction]]
        forward = ahead if ahead else options

        here = pac_dist[y][x] if is_walkable(grid, x, y) else UNREACHABLE
        sees_pac = (here != UNREACHABLE
                    and here <= self.profile.detection_range)
        if edible and here != UNREACHABLE:
            choice = self._pick(options, forward, grid, pos, pac_dist, True)
        elif sees_pac:
            choice = self._pick(options, forward, grid, pos, pac_dist, False)
        else:
            choice = self._wander(forward)
        self.direction = choice
        return choice

    def _pick(self, options: list[str], forward: list[str],
              grid: list[list[int]], pos: tuple[int, int],
              pac_dist: list[list[int]], flee: bool) -> str:
        """Chase or flee: best neighbour by distance, with rare mistakes.

        Args:
            options: Every direction that is not a wall.
            forward: Directions that do not turn back (if any).
            grid: Tile map.
            pos: ``(x, y)`` tile of the ghost.
            pac_dist: Distance field from Pac-Man.
            flee: ``True`` to get away, ``False`` to get closer.

        Returns:
            The chosen direction.
        """
        if len(forward) > 1 and self.rng.random() < self.profile.randomness:
            return self._wander(forward)
        scored: list[tuple[int, str]] = []
        for name in options:
            dx, dy = DIRECTIONS[name]
            d = pac_dist[pos[1] + dy][pos[0] + dx]
            if d != UNREACHABLE:
                scored.append((d, name))
        if not scored:
            return self._wander(forward)
        best = max(d for d, _ in scored) if flee else min(
            d for d, _ in scored)
        return self.rng.choice([n for d, n in scored if d == best])

    def _wander(self, forward: list[str]) -> str:
        """Walk around without a target and without turning back.

        Args:
            forward: Directions that do not turn back (if any).

        Returns:
            The chosen direction.
        """
        if (self.direction in forward
                and self.rng.random() < self.profile.keep_straight):
            return self.direction
        return self.rng.choice(forward)
