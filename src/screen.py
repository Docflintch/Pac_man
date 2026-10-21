#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   screen.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/07/31 06:24:04 by enchueco              #+#    #+#          #
#   Updated: 2026/07/31 06:24:04 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

"""The screens of the game: menu, game, game over / victory, highscores."""

from __future__ import annotations

import os
import sys
from typing import Any

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame  # noqa: E402

from src.perso import Enemy, Pac, Pac_gum, Scoreboard, Logo, Grid_txt  # noqa
from src.perso import Score_disp, Button, Tchat, Help  # noqa
from src.perso import Disp  # noqa: E402
from src.tools import restor_sp, grid, reachable_cells, load_scores  # noqa
from src.tools import generate_level, load_image, MazeError  # noqa: E402
from src.tools import save_score, valid_name  # noqa: E402
from src.ghost_ai import GHOST_PROFILES, distance_field  # noqa: E402
from src.panel_admin import Parameter  # noqa: E402

GEN_TRIES = 3  # number of tries when the maze generator fails


class Screen:
    """Interface of every screen."""

    def __init__(self, para: Parameter) -> None:
        """Create the screen.

        Args:
            para: Shared parameters.
        """
        self.para = para
        self.moov_screen: list[Any] = ["", False]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """React to an event.

        Args:
            event: Pygame event.

        Returns:
            ``True`` to quit the game.
        """
        return False

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Update the screen.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the screen.

        Args:
            surface: Window surface.
        """

    def enter(self) -> None:
        """Called when the screen is shown."""

    def exit(self) -> None:
        """Called when the screen is left."""


def parse_bool(msg: str) -> bool | None:
    """Read the ``True``/``False`` argument of a cheat command.

    Args:
        msg: Full command.

    Returns:
        The boolean, or ``None`` if the argument is missing or invalid.
    """
    try:
        bol = msg.split(" ")[1].lower()
    except IndexError:
        return None
    if bol == "true":
        return True
    if bol == "false":
        return False
    return None


def parse_int(msg: str) -> int | None:
    """Read the integer argument of a cheat command.

    Args:
        msg: Full command.

    Returns:
        The integer, or ``None`` if the argument is missing or invalid.
    """
    try:
        return int(msg.split(" ")[1])
    except (IndexError, ValueError):
        return None


class Menu(Screen):
    """Main menu: play, highscores, exit + cheat console."""

    def __init__(self, para: Parameter) -> None:
        """Create the menu.

        Args:
            para: Shared parameters.
        """
        super().__init__(para)
        self.sp: dict[str, Any] = {"score": [], "play": [], "logo": [],
                                   "map": [], "Pac": [], "ghost": []}
        self.tchat: Tchat | None = None
        self.help_menu: Help | None = None
        self.screen_size: tuple[int, int] = (0, 0)
        self.modif = True
        self.pac_pose = (7, 4)
        self.ghost_pos = [(7, 6), (7, 7), (7, 8), (7, 9)]
        self.map: list[list[int]] = [[0]]

    def cheat(self, msg: str) -> None:
        """Run a command of the cheat console.

        Args:
            msg: Command typed by the user.
        """
        cmd = msg.lower()
        if cmd == "/help" and self.tchat and self.help_menu:
            self.tchat.print = False
            self.help_menu.print = True
        elif cmd.startswith("/god_pac"):
            bol = parse_bool(msg)
            if bol is not None:
                self.para.god_pac = bol
        elif cmd.startswith("/speed_up"):
            value = parse_int(msg)
            if value is not None:
                self.para.speed = 1 if value <= 0 else min(value, 100)
        elif cmd.startswith("/game_more_life"):
            value = parse_int(msg)
            if value is not None:
                self.para.pac_life = max(1, min(value, 999))
        elif cmd.startswith("/game_time"):
            value = parse_int(msg)
            if value is not None:
                self.para.game_time = 60 * max(1, min(value, 600))
        elif cmd.startswith("/level_skiper"):
            bol = parse_bool(msg)
            if bol is not None:
                self.para.level_skiper = bol
        elif cmd.startswith("/dead_anim"):
            bol = parse_bool(msg)
            if bol is not None:
                self.para.dead_anim = bol
        elif cmd.startswith("/freeze_ghost"):
            bol = parse_bool(msg)
            if bol is not None:
                self.para.freeze_ghost = bol

    def handle_event(self, event: pygame.event.Event) -> bool:
        """React to the clicks, the keys and the cheat console.

        Args:
            event: Pygame event.

        Returns:
            ``True`` to quit the game.
        """
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.QUIT:
            return True

        if self.tchat is not None and self.tchat.print:
            msg = self.tchat.handle_event(event)
            if msg:
                self.cheat(msg)
            return False
        try:
            down = event.type == pygame.MOUSEBUTTONDOWN
            if self.sp["play"][5].collidepoint(mouse_pos) and down:
                if self.sp["play"][6] > 0:
                    self.sp["play"][6] = 0
                else:
                    self.sp["play"][6] = 1
                    self.moov_screen = ["play", False]
            if self.sp["score"][5].collidepoint(mouse_pos) and down:
                self.sp["score"][6] = 1
                self.moov_screen = ["score", False]

            # exit button: pressed on click, quits only if released on it
            if self.sp["exit"][5].collidepoint(mouse_pos) and down:
                self.sp["exit"][6] = 1
            if event.type == pygame.MOUSEBUTTONUP and self.sp["exit"][6] > 0:
                if self.sp["exit"][5].collidepoint(mouse_pos):
                    return True
                start = self.sp["exit"][10]
                self.sp["exit"][6] = 0
                self.sp["exit"][7] = start
                self.sp["exit"][1] = self.sp["exit"][0][start]
                self.modif = True
        except (AttributeError, IndexError):
            pass
        if event.type == pygame.KEYDOWN:
            if event.unicode == "t" and self.tchat is not None:
                self.tchat.print = True
            elif event.key == pygame.K_ESCAPE:
                if self.help_menu is not None:
                    self.help_menu.print = False
        return False

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Animate the buttons and the little pacman/ghosts of the menu.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        gw, gh = self.para.grid_size
        if self.help_menu is not None:
            self.help_menu.update(screen)
        if self.tchat is not None:
            self.tchat.update(dt, screen)
        for sp_n in self.sp.keys():  # gestion of animation

            if sp_n == "map" or sp_n == "logo":  # pass
                continue

            elif sp_n == "ghost" or sp_n == "Pac":  # anim ghosts
                for i in range(len(self.sp[sp_n])):  # all ghosts
                    # first frame of anim or after anim restarting
                    if self.sp[sp_n][i][6] == 1:
                        self.sp[sp_n][i][6] = 2
                        self.sp[sp_n][i][7] = 1
                        idx_img = self.sp[sp_n][i][7]
                        self.sp[sp_n][i][1] = self.sp[sp_n][i][0][idx_img]
                        self.modif = True
                        continue

                    self.sp[sp_n][i][8] += dt

                    # end of animation
                    if self.sp[sp_n][i][8] >= self.sp[sp_n][i][9]:
                        self.sp[sp_n][i][8] = 0
                        self.sp[sp_n][i][7] += 1
                        idx_img = self.sp[sp_n][i][7]
                        try:  # if have a other anime
                            self.sp[sp_n][i][1] = \
                                self.sp[sp_n][i][0][idx_img]
                        except IndexError:  # restart animation
                            self.sp[sp_n][i][7] = 0
                            self.sp[sp_n][i][1] = self.sp[sp_n][i][0][0]

            elif self.sp[sp_n][6] > 0:  # if animating start
                # first frame of anim or after anim restarting
                if self.sp[sp_n][6] == 1:
                    self.sp[sp_n][6] = 2
                    # frame after the start one
                    self.sp[sp_n][7] = self.sp[sp_n][10] + 1
                    idx_img = self.sp[sp_n][7]
                    self.sp[sp_n][1] = self.sp[sp_n][0][idx_img]
                    self.modif = True
                    continue

                self.sp[sp_n][8] += dt

                if self.sp[sp_n][9] < 0:  # negative delay: stay on frame
                    continue

                if self.sp[sp_n][8] >= self.sp[sp_n][9]:  # end of animation
                    self.sp[sp_n][8] = 0
                    self.sp[sp_n][7] += 1
                    idx_img = self.sp[sp_n][7]

                    try:  # if have a other anime
                        self.sp[sp_n][1] = self.sp[sp_n][0][idx_img]
                    except IndexError:  # restart animation
                        self.sp[sp_n][7] = self.sp[sp_n][10]
                        self.sp[sp_n][6] = 0
                        idx_img = self.sp[sp_n][7]
                        self.sp[sp_n][1] = self.sp[sp_n][0][idx_img]
                        self.moov_screen[1] = True
                    self.modif = True

        # restore and actualize Pacman's and ghosts' positions
        for name in ["Pac", "ghost"]:
            for i in range(len(self.sp[name])):
                ratio = self.sp[name][i][12]

                if ratio == 0:
                    x, y = self.sp[name][i][11]

                    # restore Pacman's direction
                    if self.map[y][x - 1] == 0 \
                            and self.sp[name][i][14] != "right":
                        self.sp[name][i][14] = "left"
                        if name == "Pac":
                            self.sp["Pac"][i][15] = 180
                        else:
                            self.sp[name][i][0] = \
                                self.sp[name][i][15]["left"]
                    elif self.map[y][x + 1] == 0 \
                            and self.sp[name][i][14] != "left":
                        self.sp[name][i][14] = "right"
                        if name == "Pac":
                            self.sp[name][i][15] = 0
                        else:
                            self.sp[name][i][0] = \
                                self.sp[name][i][15]["right"]
                    elif self.map[y - 1][x] == 0 \
                            and self.sp[name][i][14] != "down":
                        self.sp[name][i][14] = "up"
                        if name == "Pac":
                            self.sp[name][i][15] = 90
                        else:
                            self.sp[name][i][0] = self.sp[name][i][15]["up"]
                    elif self.map[y + 1][x] == 0 \
                            and self.sp[name][i][14] != "up":
                        self.sp[name][i][14] = "down"
                        if name == "Pac":
                            self.sp[name][i][15] = 270
                        else:
                            self.sp[name][i][0] = \
                                self.sp[name][i][15]["down"]

                if ratio >= 2:  # move for Pacman and ghosts
                    self.sp[name][i][12] = 0
                    pac_x, pac_y = self.sp[name][i][11]
                    direct = self.sp[name][i][14]

                    # move for Pacman and ghosts
                    if direct == "left":
                        pac_x -= 1
                    elif direct == "right":
                        pac_x += 1
                    elif direct == "up":
                        pac_y -= 1
                    else:
                        pac_y += 1

                    self.sp[name][i][11] = (pac_x, pac_y)

                else:  # move for ghosts and Pacman
                    size = 3
                    ox, oy, step = grid(screen, gw, gh)
                    pac_x, pac_y = self.sp[name][i][11]
                    gx, gy = pac_x * size + 9.2, pac_y * size + 0.75
                    direct = self.sp[name][i][14]

                    # move for Pacman and ghosts
                    if direct == "left":
                        gx -= ratio
                    elif direct == "right":
                        gx += ratio
                    elif direct == "up":
                        gy -= ratio
                    else:
                        gy += ratio

                    pos = (ox + gx * step, oy + gy * step)
                    self.sp[name][i][12] += self.sp[name][i][13] * dt
                    img = self.sp[name][i][1]
                    expand = self.sp[name][i][3]
                    img_size = (round(step * expand), round(step * expand))
                    if name == "Pac":
                        img = pygame.transform.rotate(img,
                                                      self.sp[name][i][15])
                    img = pygame.transform.scale(img, img_size)
                    self.sp[name][i][4] = img
                    self.sp[name][i][5] = img.get_rect(center=pos)

        if screen.get_size() == self.screen_size and not self.modif:
            return

        self.modif = False
        self.screen_size = screen.get_size()

        for sp_n in self.sp.keys():  # responcive for all except ghost and Pac
            if sp_n == "Pac" or sp_n == "ghost":
                continue
            if isinstance(self.sp[sp_n][2], list):
                for i in range(len(self.sp[sp_n][2])):
                    ox, oy, step = grid(screen, gw, gh)
                    img = self.sp[sp_n][1][i]
                    extand = self.sp[sp_n][3][i]
                    img_size = (round(step * extand), round(step * extand))
                    img = pygame.transform.scale(img, img_size)
                    if self.sp[sp_n][7][i] == 1:
                        img_w = round(img.get_width() * 0.1428)
                        img_h = img.get_height()
                    elif self.sp[sp_n][7][i] == 2:
                        img_w = img.get_width()
                        img_h = round(img.get_height() * 0.1428)
                    else:
                        img_h, img_w = img.get_size()
                    crop = pygame.Rect(0, 0, img_w, img_h)
                    img = img.subsurface(crop).copy()
                    col, row = self.sp[sp_n][2][i]
                    pos = (ox + col * step, oy + row * step)
                    try:
                        self.sp[sp_n][4][i] = img
                        if self.sp[sp_n][7][i] == 3:
                            self.sp[sp_n][5][i] = img.get_rect(topleft=pos)
                        elif self.sp[sp_n][7][i] == 4:
                            self.sp[sp_n][5][i] = img.get_rect(
                                bottomleft=pos)
                        elif self.sp[sp_n][7][i] == 5:
                            self.sp[sp_n][5][i] = img.get_rect(
                                bottomright=pos)
                        elif self.sp[sp_n][7][i] == 6:
                            self.sp[sp_n][5][i] = img.get_rect(topright=pos)
                        else:
                            self.sp[sp_n][5][i] = img.get_rect(center=pos)
                    except IndexError:
                        self.sp[sp_n][4].append(img)
                        self.sp[sp_n][5].append(img.get_rect(center=pos))
            else:
                ox, oy, step = grid(screen, gw, gh)
                col, row = self.sp[sp_n][2]
                pos = (ox + col * step, oy + row * step)
                img = self.sp[sp_n][1]
                w = round(step * self.sp[sp_n][3] / 4)
                ratio = w / img.get_width()
                h = round(img.get_height() * ratio)
                img = pygame.transform.scale(img, (w, h))
                self.sp[sp_n][4] = img
                self.sp[sp_n][5] = img.get_rect(center=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the menu.

        Args:
            screen: Window surface.
        """
        for name, sprite in self.sp.items():
            if name == "Pac" or name == "ghost":
                for i in range(len(self.sp[name])):
                    img = sprite[i][4]
                    rect = sprite[i][5]
                    if img is not None:
                        screen.blit(img, rect)
            elif isinstance(sprite[4], list):
                for s in range(len(sprite[4])):
                    img = sprite[4][s]
                    rect = sprite[5][s]
                    screen.blit(img, rect)
            else:
                img = sprite[4]
                rect = sprite[5]
                if img is not None:
                    screen.blit(img, rect)
        if self.tchat is not None:
            self.tchat.draw(screen)
        if self.help_menu is not None:
            self.help_menu.draw(screen)

    def enter(self) -> None:
        """Build every sprite of the menu."""
        self.para.reset_grid()
        gw, gh = self.para.grid_size
        self.sp = {"score": [], "play": [], "exit": [], "logo": [],
                   "map": [], "Pac": [], "ghost": []}
        self.moov_screen = ["", False]
        self.screen_size = (0, 0)
        self.modif = True
        sheet = load_image("sprite/button.png")  # detectionr button img

        line_nb_sp = [2, 13, 4]
        # score, play, exit
        screen_pos = [(gw / 3, gh - 9), (gw / 1.5, gh - 9), (4.5, 3.75)]
        screen_size = [45, 45, 30]
        # (start frame, delay)
        screen_idx_timer = [(0, 0.25), (0, 0.25), (2, -1)]
        sp_name = list(self.sp.keys())

        self.help_menu = Help((gw / 2, gh / 3.6), (gw / 1.3, gh / 1.9),
                              self.para)
        self.help_menu.enter()
        self.tchat = Tchat(100, self.para, (0, gh - 1.5), (60, 1.5))
        self.tchat.enter()

        self.map = [[3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 6],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 6, 0, 1],
                    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                    [1, 0, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, -1, 0, -2, -3, -4, -5, 0, 0, 0, 0,
                     0, 1],
                    [4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5]]

        # all button
        for y in range(3):
            start_idx, delay = screen_idx_timer[y]
            sp_stock = []
            for x in range(line_nb_sp[y]):
                rect = pygame.Rect(x * 61, y * 62, 61, 62)
                sp_stock.append(sheet.subsurface(rect).copy())
            self.sp[sp_name[y]].append(sp_stock)  # 0: frames
            self.sp[sp_name[y]].append(sp_stock[start_idx])  # 1: current img
            self.sp[sp_name[y]].append(screen_pos[y])  # 2: position
            self.sp[sp_name[y]].append(screen_size[y])  # 3: size
            for _ in range(2):
                self.sp[sp_name[y]].append(None)  # 4, 5: image, rect
            self.sp[sp_name[y]].append(0)  # 6: anim state
            self.sp[sp_name[y]].append(start_idx)  # 7: frame index
            self.sp[sp_name[y]].append(0)  # 8: timer
            self.sp[sp_name[y]].append(delay)  # 9: delay
            self.sp[sp_name[y]].append(start_idx)  # 10: start frame

        sheet = load_image("sprite/logo.png")  # detectior logo img

        self.sp["logo"].append(sheet.copy())
        self.sp["logo"].append(self.sp["logo"][0])
        self.sp["logo"].append((gw / 2, gh / 3.9))
        self.sp["logo"].append(187.5)

        for _ in range(2):
            self.sp["logo"].append(None)

        self.sp["logo"].append(False)
        all_sp = restor_sp()
        wall = all_sp["wall_roof"]
        self.sp["map"].append([])
        self.sp["map"][0].append(wall[0])  # wall left
        self.sp["map"][0].append(wall[1])  # roof top
        self.sp["map"][0].append(wall[2])  # angel top-left
        self.sp["map"][0].append(pygame.transform.rotate(wall[2], 90))
        self.sp["map"][0].append(pygame.transform.rotate(wall[2], 180))
        self.sp["map"][0].append(pygame.transform.rotate(wall[2], 270))

        for _ in range(5):
            self.sp["map"].append([])

        self.sp["map"].append(False)
        self.sp["map"].append([])

        self.sp["Pac"].append([])
        self.sp["Pac"][0].append(all_sp["PAC"]["moov"])
        self.sp["Pac"][0].append(all_sp["PAC"]["moov"][0])
        self.sp["Pac"][0].append((23.25, 15))
        self.sp["Pac"][0].append(3)

        for _ in range(2):
            self.sp["Pac"][0].append(None)

        self.sp["Pac"][0].append(2)

        for _ in range(2):
            self.sp["Pac"][0].append(0)

        self.sp["Pac"][0].append(0.1)
        self.sp["Pac"][0].append((23.25, 15))
        self.sp["Pac"][0].append((0, 0))
        self.sp["Pac"][0].append(0)
        self.sp["Pac"][0].append(20)
        self.sp["Pac"][0].append("left")
        self.sp["Pac"][0].append(20)

        for i in range(4):  # build all ghost
            self.sp["ghost"].append([])
            self.sp["ghost"][i].append(all_sp["ghost"][i]["left"])
            self.sp["ghost"][i].append(all_sp["ghost"][i]["left"][0])
            self.sp["ghost"][i].append((23.25, 15))
            self.sp["ghost"][i].append(3)
            for _ in range(2):
                self.sp["ghost"][i].append(None)
            self.sp["ghost"][i].append(2)
            for _ in range(2):
                self.sp["ghost"][i].append(0)
            self.sp["ghost"][i].append(0.1)
            self.sp["ghost"][i].append((23.25, 15))
            self.sp["ghost"][i].append((0, 0))
            self.sp["ghost"][i].append(0)
            self.sp["ghost"][i].append(20)
            self.sp["ghost"][i].append("left")
            self.sp["ghost"][i].append(all_sp["ghost"][i])

        for y in range(len(self.map)):  # restore mob or perso coord
            for x in range(len(self.map[y])):
                v = self.map[y][x]
                if v == -1:
                    self.sp["Pac"][0][11] = (x, y)
                    self.map[y][x] = 0
                elif v <= -2:
                    self.sp["ghost"][-v - 2][11] = (x, y)
                    self.map[y][x] = 0

        for y in range(len(self.map)):  # map builder
            for x in range(len(self.map[y])):
                size = 3
                sp_type = self.map[y][x] - 1
                if sp_type < 0:
                    continue
                self.sp["map"][1].append(self.sp["map"][0][sp_type])
                self.sp["map"][2].append((x * size + 9.2, y * size + 0.75))
                self.sp["map"][3].append(size)
                self.sp["map"][4].append([])
                self.sp["map"][5].append([])
                self.sp["map"][7].append(self.map[y][x])


class Game(Screen):
    """One level of the game (the same object plays every level)."""

    def __init__(self, para: Parameter) -> None:
        """Create a new game.

        Args:
            para: Shared parameters.
        """
        super().__init__(para)
        self.time_left = 0.0
        self.fright_t = 0.0
        self.cooldown: float | None = 4
        self.level = 0
        self.nb_pac_gum = 0
        self.score = 0
        self.pac_life = 0
        self.failed = False

        self.modif = True
        self.pause_on = False

        self.exit_but: Button | None = None
        self.back_but: Button | None = None
        self.player: Pac | None = None
        self.pause_disp: pygame.Surface | None = None
        self.scoreboard: Scoreboard | None = None
        self.logo: Logo | None = None
        self.countdown: Grid_txt | None = None
        self.score_disp: Score_disp | None = None
        self.time_disp: Score_disp | None = None
        self.pac_anim: Pac | None = None
        self.pac_tile: tuple[int, int] | None = None
        self.pac_dist: list[list[int]] | None = None

        self.ghost: list[Enemy] = []
        self.pac_gum: list[Pac_gum] = []
        self.gum_anim: list[Pac_gum] = []
        self.level_disp: list[Grid_txt] = []
        self.pause_txt: list[Grid_txt] = []
        self.map: list[list[int]] = [[0]]
        self.sp: dict[str, Any] = {"map": [], "life": []}

        self.screen_size = (800, 600)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Move pacman, pause, skip the level (cheat), click the buttons.

        Args:
            event: Pygame event.

        Returns:
            ``True`` to quit the game.
        """
        mouse_pos = pygame.mouse.get_pos()
        directions = {
            pygame.K_z: 90,
            pygame.K_w: 90,
            pygame.K_a: 180,
            pygame.K_q: 180,
            pygame.K_s: 270,
            pygame.K_d: 0,
            pygame.K_UP: 90,
            pygame.K_DOWN: 270,
            pygame.K_LEFT: 180,
            pygame.K_RIGHT: 0,
        }
        if event.type == pygame.QUIT:
            return True
        if self.failed or self.player is None:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in directions:
                self.player.nxt_rot = directions[event.key]
            if event.key == pygame.K_ESCAPE:
                self.toggle_pause()
            if event.key == pygame.K_n and self.para.level_skiper:
                self.level_done()

        if not self.pause_on:
            return False
        try:
            down = event.type == pygame.MOUSEBUTTONDOWN
            up = event.type == pygame.MOUSEBUTTONUP
            if self.exit_but and self.exit_but.rect:
                if self.exit_but.rect.collidepoint(mouse_pos) and down:
                    self.exit_but.idx = 1
                elif self.exit_but.rect.collidepoint(mouse_pos) and up:
                    self.exit_but.pushed = True

            if self.back_but and self.back_but.rect:
                if self.back_but.rect.collidepoint(mouse_pos) and down:
                    self.back_but.idx = 1
                elif self.back_but.rect.collidepoint(mouse_pos) and up:
                    self.back_but.pushed = True
        except AttributeError:
            pass
        return False

    def toggle_pause(self) -> None:
        """Pause or resume the game (resume starts a countdown)."""
        if self.cooldown is not None:
            return
        if self.pause_on:
            self.para.freezing = True
            self.pause_on = False
            self.cooldown = 4
        else:
            self.para.freezing = True
            self.pause_on = True

    def level_done(self) -> None:
        """Go to the next level, or to the victory screen after the last."""
        if self.level >= len(self.para.levels):
            self.para.last_score = self.score
            self.para.victory = True
            self.moov_screen = ["Game_over", True]
        else:
            self.moov_screen = ["re", True]

    def hit(self) -> None:
        """Pacman loses a life (ghost or time out)."""
        if self.player is None:
            return
        self.player.life -= 1
        self.pac_life -= 1
        self.modif = True

        if not self.para.dead_anim:
            self.player.invin_t = 0.001
        else:
            self.player.state = "dead"
            self.para.freezing = True
            self.player.frame_idx = 0
            self.player.mov = False

    def frighten(self) -> None:
        """A super pacgum is eaten: the ghosts become edible."""
        self.fright_t = self.para.frightened_time
        for g in self.ghost:
            if g.dead_t <= 0:
                g.edible = True

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Run one frame of the game.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        if self.failed or self.player is None:
            return
        gw, _ = self.para.grid_size
        ml, _ = self.para.side_margin
        if self.pause_on and self.pac_anim and self.exit_but \
                and self.back_but:
            self.pac_anim.update(dt, screen)
            self.exit_but.update(dt, screen)
            self.back_but.update(dt, screen)
            for txt in self.pause_txt:
                txt.update(screen)
            if self.back_but.continuede:
                self.moov_screen = ["menu", True]
            if self.exit_but.continuede:
                self.moov_screen = ["exit", True]
            if self.pac_anim.grid_pos[0] > gw - ml + 6:
                self.pac_anim.grid_pos = self.pac_anim.spawn_point
            for gum in self.gum_anim:
                gum.update(screen, dt)
                if gum.rect and self.pac_anim.rect \
                        and gum.rect.colliderect(self.pac_anim.rect) \
                        and gum.state == "Pacgum":
                    gum.state = "Empty"
            if self.pause_disp is None \
                    or self.pause_disp.get_size() != screen.get_size():
                self.pause_disp = pygame.Surface(screen.get_size(),
                                                 pygame.SRCALPHA)
                self.pause_disp.fill((0, 0, 0, 128))
        if self.cooldown is not None and self.cooldown > 0 \
                and not self.pause_on:
            self.cooldown -= dt
        elif self.cooldown is not None and not self.pause_on:
            self.para.freezing = False
            self.cooldown = None
        elif self.player.state == "moov" and self.para.freezing \
                and not self.pause_on:
            self.cooldown = 4
            self.fright_t = 0
            for g in self.ghost:
                g.respawn()

        running = self.cooldown is None and not self.pause_on \
            and not self.para.freezing
        if running:
            self.time_left -= dt
            if self.time_left <= 0:  # time out: lose a life, timer restart
                self.time_left = self.para.game_time
                if not self.para.god_pac:
                    self.hit()
            if self.fright_t > 0:
                self.fright_t -= dt
                if self.fright_t <= 0:
                    for g in self.ghost:
                        g.edible = False

        if self.nb_pac_gum <= 0:
            self.level_done()
        if self.player.life <= 0:
            self.para.last_score = self.score
            self.para.victory = False
            self.moov_screen = ["Game_over", True]

        self.player.update(dt, screen)

        if self.player.grid_pos != self.pac_tile:
            self.pac_tile = self.player.grid_pos
            self.pac_dist = distance_field(self.map, self.player.grid_pos)

        for i in range(len(self.ghost)):
            self.ghost[i].pac_dist = self.pac_dist
            self.ghost[i].update(dt, screen)

        for gum in self.pac_gum:
            gum.update(screen)
            if gum.state != "Empty" and gum.rect and self.player.rect \
                    and gum.rect.colliderect(self.player.rect):
                if gum.state == "Super":
                    self.score += self.para.pt_super
                    self.frighten()
                else:
                    self.score += self.para.pt_pacgum
                gum.state = "Empty"
                self.nb_pac_gum -= 1

        if self.player.state == "moov" and not self.para.invin:
            if self.player.invin_t >= self.para.t_invin_aft_hit:
                self.player.invin_t = 0
            if self.player.invin_t > 0:
                self.player.invin_t += dt

            for ghost in self.ghost:
                if ghost.dead_t > 0 or ghost.rect is None \
                        or self.player.rect is None:
                    continue
                if not ghost.rect.colliderect(self.player.rect):
                    continue
                if self.pause_on or self.cooldown is not None:
                    continue
                if ghost.edible:
                    ghost.die()
                    self.score += self.para.pt_ghost
                elif self.player.invin_t == 0 and not self.para.god_pac \
                        and self.player.state == "moov":
                    self.hit()

        if self.countdown and self.cooldown is not None \
                and self.cooldown > 0:
            self.countdown.txt = str(int(self.cooldown))
            self.countdown.update(screen)

        if self.logo:
            self.logo.update(screen)
        if self.scoreboard:
            self.scoreboard.update(screen)
        if self.score_disp:
            self.score_disp.update(screen, self.score)
        if self.time_disp:
            left = max(0, int(self.time_left + 0.999))
            self.time_disp.update(screen, f"{left // 60}:{left % 60:02d}")
        for lvl in self.level_disp:
            lvl.update(screen)
        if screen.get_size() == self.screen_size and not self.modif:
            return

        self.screen_size = screen.get_size()
        self.modif = False

        wid, hei = self.para.grid_size
        ox, oy, step = grid(screen, wid, hei)
        for i in range(len(self.sp["map"][2])):
            img = self.sp["map"][1][i]
            size = (round(step), round(step))
            img = pygame.transform.scale(img, size)
            if self.sp["map"][7][i] == 1:
                img_w, img_h = round(img.get_width() * 0.1428), \
                    img.get_height()
            elif self.sp["map"][7][i] == 2:
                img_w, img_h = img.get_width(), \
                    round(img.get_height() * 0.1428)
            else:
                img_w, img_h = img.get_size()
            crop = pygame.Rect(0, 0, img_w, img_h)
            img = img.subsurface(crop).copy()
            col, row = self.sp["map"][2][i]
            pos = (ox + col * step, oy + row * step)
            try:
                self.sp["map"][4][i] = img
                if self.sp["map"][7][i] == 3:
                    self.sp["map"][5][i] = img.get_rect(topleft=pos)
                elif self.sp["map"][7][i] == 4:
                    self.sp["map"][5][i] = img.get_rect(bottomleft=pos)
                elif self.sp["map"][7][i] == 5:
                    self.sp["map"][5][i] = img.get_rect(bottomright=pos)
                elif self.sp["map"][7][i] == 6:
                    self.sp["map"][5][i] = img.get_rect(topright=pos)
                else:
                    self.sp["map"][5][i] = img.get_rect(center=pos)
            except IndexError:
                self.sp["map"][4].append(img)
                self.sp["map"][5].append(img.get_rect(center=pos))

        grid_col, grid_row = self.para.grid_size
        self.sp["life"][2] = []
        for i in range(self.player.life):
            if i >= 24:
                break
            img = self.sp["life"][0]
            col, row = (grid_col - 4 - i % 6, grid_row - 2 - int(i / 6))
            pos = (ox + col * step, oy + row * step)
            size = (round(step), round(step))
            img = pygame.transform.scale(img, size)
            self.sp["life"][1] = img
            self.sp["life"][2].append(img.get_rect(center=pos))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the game, the HUD and the pause menu.

        Args:
            screen: Window surface.
        """
        if self.failed or self.player is None:
            return
        for i in range(len(self.sp["map"][4])):
            img = self.sp["map"][4][i]
            rect = self.sp["map"][5][i]
            screen.blit(img, rect)
        for gum in self.pac_gum:
            gum.draw(screen)
        for i in range(len(self.ghost)):
            self.ghost[i].draw(screen)
        self.player.draw(screen)
        for i in range(len(self.sp["life"][2])):
            img = self.sp["life"][1]
            rect = self.sp["life"][2][i]
            screen.blit(img, rect)
        if self.scoreboard:
            self.scoreboard.draw(screen)
        if self.logo:
            self.logo.draw(screen)
        if self.countdown and self.cooldown is not None \
                and self.cooldown > 0:
            self.countdown.draw(screen)
        if self.score_disp:
            self.score_disp.draw(screen)
        if self.time_disp:
            self.time_disp.draw(screen)
        for lvl in self.level_disp:
            lvl.draw(screen)
        if self.pause_disp is not None and self.pause_on \
                and self.pac_anim and self.exit_but and self.back_but:
            screen.blit(self.pause_disp, (0, 0))
            for gum in self.gum_anim:
                gum.draw(screen)
            self.pac_anim.draw(screen)
            self.exit_but.draw(screen)
            self.back_but.draw(screen)
            for txt in self.pause_txt:
                txt.draw(screen)

    def make_map(self) -> bool:
        """Generate the maze of the current level.

        The first level uses the config seed, the others are random (unless
        the level has its own ``seed``).

        Returns:
            ``False`` if the generator failed every time.
        """
        lvl = self.para.levels[min(self.level, len(self.para.levels)) - 1]
        if "seed" in lvl:
            seed = lvl["seed"]
        else:
            seed = self.para.seed if self.level == 1 else 0
        for i in range(GEN_TRIES):
            try:
                self.map = generate_level(lvl["width"], lvl["height"], seed)
                return True
            except MazeError as exc:
                print(f"Error: level {self.level}: {exc} (try {i + 1}/"
                      f"{GEN_TRIES})", file=sys.stderr)
                seed = 0
        return False

    def enter(self) -> None:
        """Build the next level (score and lives are kept)."""
        self.level += 1
        self.pause_on = False
        self.fright_t = 0
        self.time_left = self.para.game_time
        self.pac_tile = None
        self.pac_dist = None

        if not self.make_map():
            print("Error: the maze generator failed, back to the menu",
                  file=sys.stderr)
            self.failed = True
            self.moov_screen = ["menu", True]
            return
        self.para.set_map_size(len(self.map[0]), len(self.map))

        gw, gh = self.para.grid_size
        mt, mb = self.para.vertical_margin
        ml, mr = self.para.side_margin
        of_x, of_y = self.para.map_offset
        self.level_disp = []
        for i, txt in enumerate(["-- LEVEL --",
                                 f"{self.level}/{len(self.para.levels)}"]):
            class_txt = Grid_txt(txt, (gw - mr / 2, mt + 4.5 + i * 3),
                                 self.para, 2.25)
            self.level_disp.append(class_txt)
        self.scoreboard = Scoreboard(self.para)
        self.scoreboard.enter()
        self.countdown = Grid_txt("3", (gw / 2, gh / 2), self.para, 15)
        self.score_disp = Score_disp(self.para)
        self.score_disp.enter()
        self.time_disp = Score_disp(self.para, "--- Time ---", 19.5, "{}")
        self.time_disp.enter()

        sheet = load_image("sprite/button.png")  # detectionr button img

        all_sp = restor_sp()

        sprite = []
        for x in range(4):
            rect = pygame.Rect(x * 61, 2 * 62, 61, 62)
            sprite.append(sheet.subsurface(rect).copy())
        self.back_but = Button(sprite[:2], (gw - 7, 0), self.para, (7, 7))
        self.exit_but = Button(sprite[2:], (0, 0), self.para, (7, 7))
        self.pause_txt = [
            Grid_txt("PAUSE", (gw / 2, gh / 4), self.para, 6),
            Grid_txt("QUIT", (3.5, 8.5), self.para, 1.5),
            Grid_txt("MENU", (gw - 3.5, 8.5), self.para, 1.5),
        ]
        anim_para = Parameter()
        anim_para.grid_size = self.para.grid_size
        anim_para.freezing = False
        self.pac_anim = Pac(all_sp["PAC"], (-ml - 6, gh / 2 - mt), anim_para,
                            (9, 9))
        self.pac_anim.free = True
        self.gum_anim = []
        for i in range(8):
            gum_sp = all_sp["obj"]["Pacgum"][0]
            self.gum_anim.append(Pac_gum(gum_sp,
                                         (0 + i * 12 - ml, gh / 2 - mt),
                                         anim_para))
            self.gum_anim[i].size = (9, 9)

        self.sp["life"] = []
        self.sp["life"].append(all_sp["obj"]["life"][0])
        self.sp["life"].append(None)
        self.sp["life"].append([])

        sheet = load_image("sprite/logo.png")  # detectior logo img
        size = (gw - (ml + mr) - 2, mt + 9)
        self.logo = Logo(sheet, (gw / 2, 3), size, self.para)

        self.ghost = []
        self.pac_gum = []
        self.nb_pac_gum = 0
        wall = all_sp["wall_roof"]
        self.sp["map"] = []  # map manag
        self.sp["map"].append([])
        self.sp["map"][0].append(wall[0])  # wall left
        self.sp["map"][0].append(wall[1])  # roof top
        self.sp["map"][0].append(wall[2])  # angel top-left
        self.sp["map"][0].append(pygame.transform.rotate(wall[2], 90))
        self.sp["map"][0].append(pygame.transform.rotate(wall[2], 180))
        self.sp["map"][0].append(pygame.transform.rotate(wall[2], 270))

        for _ in range(5):
            self.sp["map"].append([])

        self.sp["map"].append(False)
        self.sp["map"].append([])

        spawn = (0, 0)
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                if self.map[y][x] == -1:
                    spawn = (x, y)

        # recharbel grid pos
        rgp = reachable_cells(self.map, spawn)

        for y in range(len(self.map)):  # map builder
            for x in range(len(self.map[y])):
                sp_type = self.map[y][x] - 1
                if sp_type < 0:
                    if sp_type == -1 and (x, y) in rgp:
                        gum_sp = all_sp["obj"]["Pacgum"][0]
                        self.pac_gum.append(Pac_gum(gum_sp, (x, y),
                                                    self.para))
                        self.nb_pac_gum += 1
                    elif sp_type == -1:
                        continue
                    elif sp_type == -2:
                        self.player = Pac(all_sp["PAC"], (x, y), self.para)
                        if self.pac_life > 0:
                            self.player.life = self.pac_life
                        self.pac_life = self.player.life
                    elif -6 <= sp_type <= -3:
                        gt = -sp_type - 3
                        self.ghost.append(Enemy(self.para.ghost_speed,
                                                all_sp["ghost"][gt], (x, y),
                                                self.para, GHOST_PROFILES[gt]))
                    elif sp_type == -7:  # super pacgum
                        gum_sp = all_sp["obj"]["Super_Pacgum"][0]
                        gum = Pac_gum(gum_sp, (x, y), self.para,
                                      state="Super")
                        gum.size = (1.6, 1.6)
                        self.pac_gum.append(gum)
                        self.nb_pac_gum += 1
                    continue
                self.sp["map"][1].append(self.sp["map"][0][sp_type])
                self.sp["map"][2].append((x + ml + of_x, y + mt + of_y))
                self.sp["map"][3].append(4)
                self.sp["map"][4].append([])
                self.sp["map"][5].append([])
                self.sp["map"][7].append(self.map[y][x])

        if self.player is not None:
            self.player.map = self.map
        for ghost in self.ghost:
            ghost.map = self.map

    def exit(self) -> None:
        """Freeze everything before the next level / screen."""
        self.cooldown = 4
        self.para.freezing = True
        self.moov_screen = ["", False]
        self.modif = True


class Game_over(Screen):
    """Game over / victory screen: final score and name for highscores."""

    def __init__(self, para: Parameter) -> None:
        """Create the screen.

        Args:
            para: Shared parameters.
        """
        super().__init__(para)
        self.texts: list[Grid_txt] = []
        self.error_txt: Grid_txt | None = None
        self.tchat: Tchat | None = None
        self.box: Disp | None = None
        self.banner: Logo | None = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Type the name, ENTER to save, ESC to skip.

        Args:
            event: Pygame event.

        Returns:
            ``True`` to quit the game.
        """
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.moov_screen = ["menu", True]
            return False
        if self.tchat is None:
            return False
        msg = self.tchat.handle_event(event)
        if msg is None:
            return False
        name = msg.strip()
        if valid_name(name):
            save_score(self.para.highscore_file, name, self.para.last_score)
            self.moov_screen = ["menu", True]
        elif self.error_txt is not None:
            self.error_txt.txt = "1 to 10 letters, digits or spaces !"
        return False

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Resize everything.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        if self.banner:
            self.banner.update(screen)
        for txt in self.texts:
            txt.update(screen)
        if self.error_txt:
            self.error_txt.update(screen)
        if self.box:
            self.box.update(screen)
        if self.tchat:
            self.tchat.update(dt, screen)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the screen.

        Args:
            surface: Window surface.
        """
        if self.banner:
            self.banner.draw(surface)
        for txt in self.texts:
            txt.draw(surface)
        if self.error_txt:
            self.error_txt.draw(surface)
        if self.box:
            self.box.draw(surface)
        if self.tchat:
            self.tchat.draw(surface)

    def enter(self) -> None:
        """Build the screen for a victory or a defeat."""
        self.para.reset_grid()
        self.moov_screen = ["", False]
        gw, gh = self.para.grid_size
        sheet = load_image("sprite/Victoire et Défaite.png")
        if self.para.victory:
            crop = pygame.Rect(0, 0, 332, 178)
            title = "CONGRATULATIONS, YOU WIN !"
            color = (255, 230, 0)
        else:
            crop = pygame.Rect(333, 0, 318, 178)
            title = "GAME OVER"
            color = (255, 70, 40)
        self.banner = Logo(sheet.subsurface(crop).copy(), (gw / 2, 11),
                           (30, 16), self.para)
        self.texts = [
            Grid_txt(title, (gw / 2, 22), self.para, 2.5, color),
            Grid_txt(f"FINAL SCORE : {self.para.last_score}", (gw / 2, 26),
                     self.para, 2.25),
            Grid_txt("ENTER YOUR NAME :", (gw / 2, 30), self.para, 1.8),
            Grid_txt("ENTER : save        ESC : skip", (gw / 2, 42),
                     self.para, 1.5, (180, 180, 180)),
        ]
        self.error_txt = Grid_txt("", (gw / 2, 37.5), self.para, 1.5,
                                  (255, 70, 40))
        self.box = Disp((gw / 2, 33.5), (18.6, 3.6), self.para,
                        (40, 40, 90, 255))
        self.tchat = Tchat(10, self.para, (gw / 2 - 9, 32), (18, 3))
        self.tchat.enter()
        self.tchat.print = True
        self.tchat.allowed = lambda c: c.isalnum() or c == " "


class Score(Screen):
    """Top 10 highscores."""

    def __init__(self, para: Parameter) -> None:
        """Create the screen.

        Args:
            para: Shared parameters.
        """
        super().__init__(para)
        self.title: Grid_txt | None = None
        self.ranking: list[Grid_txt] = []
        self.button: Button | None = None
        self.pushed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Click on the back button (or ESC) to go back to the menu.

        Args:
            event: Pygame event.

        Returns:
            ``True`` to quit the game.
        """
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.moov_screen = ["menu", True]
        if self.button is None or self.button.rect is None:
            return False
        if self.button.rect.collidepoint(mouse_pos) \
                and event.type == pygame.MOUSEBUTTONDOWN:
            self.button.idx = 1
        elif self.button.rect.collidepoint(mouse_pos) \
                and event.type == pygame.MOUSEBUTTONUP:
            self.button.pushed = True
        return False

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Resize everything.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        if self.button is None or self.title is None:
            return
        if self.button.continuede:
            self.moov_screen = ["menu", True]
        self.title.update(screen)
        self.button.update(dt, screen)
        for rank in self.ranking:
            rank.update(screen)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the screen.

        Args:
            surface: Window surface.
        """
        if self.button is None or self.title is None:
            return
        self.title.draw(surface)
        self.button.draw(surface)
        for rank in self.ranking:
            rank.draw(surface)

    def enter(self) -> None:
        """Load the highscores and build the texts."""
        self.para.reset_grid()
        gw, _ = self.para.grid_size
        self.title = Grid_txt("Score_Board", (gw / 2, 4.5), self.para, 7.5)
        sorted_sc = load_scores(self.para.highscore_file)
        self.ranking = []
        right_left = False
        for i in range(10):
            if i >= len(sorted_sc):
                score = "xxxxxxxxxx - xxxxxx"
            else:
                nbr_score = min(sorted_sc[i]['score'], 999999)
                score = f"{sorted_sc[i]['name'][:10]} - {nbr_score}"

            x = 0
            y = int(i / 2)
            if right_left:
                self.ranking.append(Grid_txt("|", (gw / 2, 10.5 + 5 * i),
                                             self.para, 10.5))
                x = gw - 30
                right_left = False
            else:
                right_left = True
            txt = f"{i + 1}. {score}"
            self.ranking.append(Grid_txt(txt, (x + 15, 15 + 6 * y),
                                         self.para, 2.1))

        sheet = load_image("sprite/button.png")  # detectionr button img

        sprite = []
        for x in range(2):
            rect = pygame.Rect(x * 61, 2 * 62, 61, 62)
            sprite.append(sheet.subsurface(rect).copy())
        self.button = Button(sprite, (1.5, 1.5), self.para, (6, 6))
