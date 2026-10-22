#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   panel_admin.py                                       :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/07/30 05:02:41 by enchueco              #+#    #+#          #
#   Updated: 2026/07/30 05:02:41 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

"""Shared parameters of the game (config values + cheat values)."""

from __future__ import annotations

from typing import Any

from src.config import NUMBERS, DEFAULT_LEVEL, MIN_LEVELS, DEFAULT_HIGHSCORE

MAP_AREA = 37  # default size (in tiles) of the maze area


class Parameter:
    """Every value shared between the screens."""

    def __init__(self, conf: dict[str, Any] | None = None) -> None:
        """Create the parameters.

        Args:
            conf: Result of ``load_config`` (``None`` = default values).
        """
        if conf is None:
            conf = {key: val[0] for key, val in NUMBERS.items()}
            conf["levels"] = [dict(DEFAULT_LEVEL) for _ in range(MIN_LEVELS)]
            conf["highscore_filename"] = DEFAULT_HIGHSCORE

        self.side_margin = (18, 18)  # (marge_left, marge_right)
        self.vertical_margin = (9, 0)  # (marge_top, marge_buttom)
        self.map_offset = (0, 0)  # center small maze in the maze area
        self.grid_size = (0, 0)  # size of the grid for responcive
        self.reset_grid()

        self.t_invin_aft_hit = 2  # time of invincibility after hit (in sec)
        self.invin = False
        self.dead_speed_anim = 0.2

        # config
        self.levels: list[dict[str, int]] = conf["levels"]
        self.seed: int = conf["seed"]
        self.highscore_file: str = conf["highscore_filename"]
        self.nb_pacgum: int = conf["pacgum"]
        self.pt_pacgum: int = conf["points_per_pacgum"]
        self.pt_super: int = conf["points_per_super_pacgum"]
        self.pt_ghost: int = conf["points_per_ghost"]
        self.ghost_speed: float = conf["ghost_speed"]
        self.frightened_time: float = conf["frightened_time"]
        self.respawn_time: float = conf["ghost_respawn_time"]

        # tcheat
        self.god_pac = False
        self.speed: float = conf["pacman_speed"]  # speed of the pacman
        self.pac_life: int = conf["lives"]
        self.game_time: float = conf["level_max_time"]  # in second
        self.level_skiper = False
        self.dead_anim = True
        self.freeze_ghost = False

        self.freezing = True

        # result of the last game (for the game over screen)
        self.last_score = 0
        self.victory = False

    def set_map_size(self, tiles_w: int, tiles_h: int) -> None:
        """Resize the grid so a maze of ``tiles_w`` x ``tiles_h`` fits.

        Args:
            tiles_w: Width of the tile map.
            tiles_h: Height of the tile map.
        """
        area_w = max(tiles_w, MAP_AREA)
        area_h = max(tiles_h, MAP_AREA)
        side_marg = self.side_margin[0] + self.side_margin[1]
        verti_marg = self.vertical_margin[0] + self.vertical_margin[1]
        self.grid_size = (area_w + side_marg, area_h + verti_marg)
        self.map_offset = ((area_w - tiles_w) // 2, (area_h - tiles_h) // 2)

    def reset_grid(self) -> None:
        """Go back to the default grid (used by the menus)."""
        self.set_map_size(MAP_AREA, MAP_AREA)
