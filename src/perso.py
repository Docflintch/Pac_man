#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   perso.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/08/02 03:38:09 by enchueco              #+#    #+#          #
#   Updated: 2026/08/02 03:38:09 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #
"""Every object drawn on the screens (characters, texts, buttons...)."""

from __future__ import annotations

import os
from typing import Any, Callable

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame  # noqa: E402

from src.tools import grid, load_scores  # noqa: E402
from src.panel_admin import Parameter  # noqa: E402
from src.ghost_ai import GhostBrain, GhostProfile  # noqa: E402

CHEAT_HELP = [
    "/God_Pac True/False: Pacman becomes a god, he takes no damage",
    "/Speed_up [value (int)]: speed of pacman | max_value = 100",
    "/game_more_life [value (int)]: set pac life (max_disp 24)",
    "/level_skiper True/False: if True push \"n\" in game to skip the level",
    "/game_time [value (int)]: time of each level in min",
    "/dead_anim True/False: deactivate dead anim for continue where you are",
    "/freeze_ghost True/False: the ghosts stop moving",
    "",
    "for reset all value at defalt you had to restart",
]


class CharacterOutline:
    """Common part of Pac-Man and the ghosts."""

    def __init__(self, speed: float, sprite: dict[str, list[Any]]) -> None:
        """Store the speed and the animations.

        Args:
            speed: Speed in tiles per second.
            sprite: Animations, by name.
        """
        self.sprite = sprite
        self.state: str = ""
        self.frame_idx = 0
        self.speed = speed


class Enemy(CharacterOutline):
    """A ghost, moved by a ``GhostBrain``."""

    def __init__(self, speed: float, sprite: dict[str, list[Any]],
                 pos: tuple[int, int], para: Parameter,
                 profile: GhostProfile) -> None:
        """Create a ghost on its spawn tile.

        Args:
            speed: Speed in tiles per second.
            sprite: Animations of this ghost.
            pos: Spawn tile.
            para: Shared parameters.
            profile: Behaviour of the ghost.
        """
        super().__init__(speed, sprite)
        self.spawn_point = pos
        self.state = "up"
        self.anim = 0.0
        self.ratio = 0.0
        self.now_img = self.sprite[self.state][0]
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self.grid_pos = pos
        self.para = para
        self.map: list[list[int]] = [[0]]
        self.brain = GhostBrain(profile)
        self.pac_dist: list[list[int]] | None = None
        self.edible = False
        self.dead_t = 0.0

    def die(self) -> None:
        """The ghost is eaten: hide it until it respawns."""
        self.dead_t = self.para.respawn_time
        self.edible = False

    def respawn(self) -> None:
        """Put the ghost back on its corner."""
        self.dead_t = 0
        self.grid_pos = self.spawn_point
        self.ratio = 0
        self.edible = False

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Animate, move and resize the ghost.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        frozen = self.para.freezing or self.para.freeze_ghost
        if self.dead_t > 0:
            if not self.para.freezing:
                self.dead_t -= dt
                if self.dead_t <= 0:
                    self.respawn()
            return
        anim_name = "scared" if self.edible else self.state
        if not frozen:
            self.anim += dt
            if self.anim >= 0.1:
                self.anim = 0
                self.frame_idx += 1
                try:
                    self.now_img = self.sprite[anim_name][self.frame_idx]
                except IndexError:
                    self.frame_idx = 0
                    self.now_img = self.sprite[anim_name][self.frame_idx]

        if self.ratio == 0 and not frozen and self.pac_dist is not None:
            self.state = self.brain.decide(self.map, self.grid_pos,
                                           self.pac_dist, self.edible)
        if self.ratio >= 1:
            self.ratio = 0
            g_x, g_y = self.grid_pos

            if self.state == "left":
                g_x -= 1
            elif self.state == "right":
                g_x += 1
            elif self.state == "up":
                g_y -= 1
            else:
                g_y += 1
            self.grid_pos = (g_x, g_y)
        else:
            wid, hei = self.para.grid_size
            ox, oy, step = grid(screen, wid, hei)
            gx: float
            gy: float
            gx, gy = self.grid_pos
            m_l, _ = self.para.side_margin
            m_t, _ = self.para.vertical_margin
            of_x, of_y = self.para.map_offset
            gx += m_l + of_x
            gy += m_t + of_y

            if self.state == "left":
                gx -= self.ratio
            elif self.state == "right":
                gx += self.ratio
            elif self.state == "up":
                gy -= self.ratio
            else:
                gy += self.ratio

            pos = (ox + gx * step, oy + gy * step)
            if not frozen:
                speed = self.speed * (0.6 if self.edible else 1)
                self.ratio += speed * dt
            img = self.now_img
            size = (round(step / 1.2), round(step / 1.2))
            img = pygame.transform.scale(img, size)
            self.image = img
            self.rect = img.get_rect(center=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the ghost (not while it is eaten).

        Args:
            screen: Window surface.
        """
        if self.dead_t > 0 or self.image is None or self.rect is None:
            return
        screen.blit(self.image, self.rect)


class Pac(CharacterOutline):
    """Pac-Man, moved by the player."""

    def __init__(self, sprite: dict[str, list[Any]], pos: tuple[float, float],
                 para: Parameter,
                 size: tuple[float, float] | None = None) -> None:
        """Create Pac-Man on its spawn tile.

        Args:
            sprite: Animations of Pac-Man.
            pos: Spawn tile.
            para: Shared parameters.
            size: Size in tiles (``None`` = 1 tile).
        """
        super().__init__(para.speed, sprite)
        self.spawn_point = pos
        self.state = "moov"
        self.anim = 0.0
        self.rotate = 0
        self.nxt_rot = 0
        self.ratio = 0.0
        self.now_img = self.sprite[self.state][0]
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self.grid_pos: tuple[Any, Any] = pos
        self.para = para
        self.life: int = self.para.pac_life
        self.mov = False
        self.map: list[list[int]] = [[0]]
        self.invin_t = 0.0
        self.grid_size = size
        self.free = False

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Animate, move and resize Pac-Man.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        self.speed = self.para.speed
        self.anim += dt

        dead_time = 0.0
        if self.state == "dead":
            dead_time = self.para.dead_speed_anim
        if self.anim >= 0.1 + dead_time:
            self.anim = 0
            if not self.para.freezing or self.state == "dead":
                self.frame_idx += 1
                frames = self.sprite[self.state]
                if self.frame_idx >= len(frames):
                    self.frame_idx = 0
                    if self.state == "dead":
                        self.grid_pos = self.spawn_point
                        self.ratio = 0
                        self.mov = False
                        self.state = "moov"
                        frames = self.sprite["moov"]
                self.now_img = frames[self.frame_idx]

        if not self.para.freezing:  # manege all directions
            opposit = {
                90: 270,
                270: 90,
                0: 180,
                180: 0
            }
            x, y = self.grid_pos
            if self.nxt_rot == 90:
                y -= 1
            elif self.nxt_rot == 270:
                y += 1
            elif self.nxt_rot == 180:
                x -= 1
            elif self.nxt_rot == 0:
                x += 1

            if self.free:
                self.mov = True
            elif 0 <= y < len(self.map) and 0 <= x < len(self.map[y]) \
                    and self.map[y][x] <= 0 and self.ratio <= 0.4:
                self.mov = True
                if opposit[self.nxt_rot] == self.rotate:
                    self.ratio = -self.ratio
                self.rotate = self.nxt_rot
            else:
                x, y = self.grid_pos
                if self.rotate == 90:
                    y -= 1
                elif self.rotate == 270:
                    y += 1
                elif self.rotate == 180:
                    x -= 1
                elif self.rotate == 0:
                    x += 1

                if 0 <= y < len(self.map) and 0 <= x < len(self.map[y]) \
                        and self.map[y][x] <= 0:
                    self.mov = True
                else:
                    self.mov = False

        if self.ratio >= 1:
            self.ratio = 0
            pac_x, pac_y = self.grid_pos

            if self.rotate == 180:
                pac_x -= 1
            elif self.rotate == 0:
                pac_x += 1
            elif self.rotate == 90:
                pac_y -= 1
            else:
                pac_y += 1
            self.grid_pos = (pac_x, pac_y)
        else:
            wid, hei = self.para.grid_size
            ox, oy, step = grid(screen, wid, hei)
            gx, gy = self.grid_pos
            m_l, _ = self.para.side_margin
            m_t, _ = self.para.vertical_margin
            of_x, of_y = self.para.map_offset
            gx += m_l + of_x
            gy += m_t + of_y

            if self.rotate == 180:
                gx -= self.ratio
            elif self.rotate == 0:
                gx += self.ratio
            elif self.rotate == 90:
                gy -= self.ratio
            else:
                gy += self.ratio

            pos = (ox + gx * step, oy + gy * step)
            if self.mov and not self.para.freezing:
                self.ratio += self.speed * dt
            img = self.now_img
            if self.grid_size is not None:
                s_w, s_h = self.grid_size
                size = (round(s_w * step), round(s_h * step))
            else:
                size = (round(step), round(step))
            img = pygame.transform.rotate(img, self.rotate)
            img = pygame.transform.scale(img, size)
            self.image = img
            self.rect = img.get_rect(center=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw Pac-Man.

        Args:
            screen: Window surface.
        """
        if self.image is not None and self.rect is not None:
            screen.blit(self.image, self.rect)


class Pac_gum:
    """A pacgum or a super pacgum."""

    def __init__(self, sprite: pygame.Surface, pos: tuple[float, float],
                 para: Parameter, cooldown: float = 2,
                 state: str = "Pacgum") -> None:
        """Create a pacgum.

        Args:
            sprite: Image of the pacgum.
            pos: Tile of the pacgum.
            para: Shared parameters.
            cooldown: Time before an eaten pacgum of the pause animation
                comes back.
            state: ``"Pacgum"`` or ``"Super"``.
        """
        self.sprite = sprite
        self.state = state
        self.full_state = state
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self.grid_pos = pos
        self.para = para
        self.timer = 0.0
        self.cooldown = cooldown
        self.screen_size: tuple[int, int] | None = None
        self.size: tuple[float, float] | None = None

    def update(self, screen: pygame.Surface, dt: float = 0) -> None:
        """Respawn (pause animation only) and resize the pacgum.

        Args:
            screen: Window surface.
            dt: Time since the last frame (0 = never respawn).
        """
        if self.state == "Empty":
            self.timer += dt
            if self.timer >= self.cooldown and dt > 0:
                self.timer = 0
                self.state = self.full_state
        wid, hei = self.para.grid_size

        if self.screen_size == screen.get_size():
            return
        self.screen_size = screen.get_size()
        ox, oy, step = grid(screen, wid, hei)
        gx, gy = self.grid_pos
        m_l, _ = self.para.side_margin
        m_t, _ = self.para.vertical_margin
        of_x, of_y = self.para.map_offset
        gx += m_l + of_x
        gy += m_t + of_y

        pos = (ox + gx * step, oy + gy * step)
        img = self.sprite
        s_w, s_h = 1.0, 1.0
        if self.size is not None:
            s_w, s_h = self.size
        size = (max(1, round(s_w * step / 2)), max(1, round(s_h * step / 2)))
        img = pygame.transform.scale(img, size)
        self.image = img
        self.rect = img.get_rect(center=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the pacgum if it is not eaten.

        Args:
            screen: Window surface.
        """
        if self.state == "Empty" or self.image is None or self.rect is None:
            return
        screen.blit(self.image, self.rect)


class Grid_txt:
    """A text placed on the grid."""

    def __init__(self, txt: str, pos: tuple[float, float], para: Parameter,
                 height: float = 1.0,
                 color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """Create a text.

        Args:
            txt: Text to show.
            pos: Position on the grid.
            para: Shared parameters.
            height: Height of the font, in tiles.
            color: RGB color.
        """
        self.txt = txt
        self.grid_pos = pos
        self.height = height
        self.color = color
        self.font_path = "./font/pixel_font.ttf"
        self.para = para
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self._key: tuple[Any, ...] | None = None
        self._font: pygame.font.Font | None = None
        self._font_size = 0
        self.max_len: int | None = None
        self.anchor = "center"

    def update(self, screen: pygame.Surface) -> None:
        """Render the text again if it or the window changed.

        Args:
            screen: Window surface.
        """
        if self.max_len is not None:
            self.txt = self.txt[:self.max_len]
        key = (self.txt, screen.get_size(), self.para.grid_size, self.color)

        if key == self._key:
            return

        self._key = key
        wid, hei = self.para.grid_size
        ox, oy, step = grid(screen, wid, hei)

        size = max(1, round(step * self.height))

        if size != self._font_size or self._font is None:
            try:
                self._font = pygame.font.Font(self.font_path, size)
            except (FileNotFoundError, OSError, pygame.error):
                self._font = pygame.font.Font(None, size)
            self._font_size = size

        self.image = self._font.render(self.txt, False, self.color)
        col, row = self.grid_pos
        pos = (ox + col * step, oy + row * step)
        self.rect = self.image.get_rect(**{self.anchor: pos})

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the text.

        Args:
            screen: Window surface.
        """
        if self.image and self.rect:
            screen.blit(self.image, self.rect)


class Scoreboard:
    """Small top 10 shown on the left of the game."""

    def __init__(self, para: Parameter) -> None:
        """Create the scoreboard.

        Args:
            para: Shared parameters.
        """
        self.title: Grid_txt | None = None
        self.lines: list[Grid_txt] = []
        self.para = para

    def update(self, screen: pygame.Surface) -> None:
        """Resize the texts.

        Args:
            screen: Window surface.
        """
        if self.title is not None:
            self.title.update(screen)
        for line in self.lines:
            line.update(screen)

    def enter(self) -> None:
        """Load the highscores and build the texts."""
        m_t, _ = self.para.vertical_margin
        self.title = Grid_txt("Score_Board", (9, 4.5 + m_t), self.para, 2.25)
        sorted_sc = load_scores(self.para.highscore_file)
        self.lines = []
        for i in range(10):
            if i >= len(sorted_sc):
                score = "xxxx - xxxxxx"
            else:
                nbr_score = min(sorted_sc[i]['score'], 999999)
                score = f"{sorted_sc[i]['name'][:4]} - {nbr_score}"

            self.lines.append(Grid_txt(f"{i + 1}. {score}",
                                       (9, 3 * i + m_t + 8), self.para, 1.5))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the scoreboard.

        Args:
            screen: Window surface.
        """
        if self.title is not None:
            self.title.draw(screen)
        for line in self.lines:
            line.draw(screen)


class Logo:
    """An image placed on the grid, keeping its ratio."""

    def __init__(self, sprite: pygame.Surface, pos: tuple[float, float],
                 size: tuple[float, float], para: Parameter) -> None:
        """Create the image.

        Args:
            sprite: Image.
            pos: Center on the grid.
            size: Size in tiles (only the width is used).
            para: Shared parameters.
        """
        self.sprite = sprite
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self.grid_pos = pos
        self.grid_size = size
        self.para = para

    def update(self, screen: pygame.Surface) -> None:
        """Resize the image.

        Args:
            screen: Window surface.
        """
        wid, hei = self.para.grid_size
        ox, oy, step = grid(screen, wid, hei)
        gx, gy = self.grid_pos

        pos = (ox + gx * step, oy + gy * step)
        lw, _ = self.grid_size
        w = round(lw * step)
        h = round(self.sprite.get_height() * w / self.sprite.get_width())
        img = pygame.transform.scale(self.sprite, (w, h))
        self.image = img
        self.rect = img.get_rect(center=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the image.

        Args:
            screen: Window surface.
        """
        if self.image is not None and self.rect is not None:
            screen.blit(self.image, self.rect)


class Score_disp:
    """A title and a value on the right of the game (score, time...)."""

    def __init__(self, para: Parameter, title: str = "--- Score ---",
                 row: float = 12, fmt: str = "{} pt") -> None:
        """Create the display.

        Args:
            para: Shared parameters.
            title: Title text.
            row: Row of the title (under the top margin).
            fmt: Format of the value.
        """
        self.l_score: list[Grid_txt] = []
        self.para = para
        self.title = title
        self.row = row
        self.fmt = fmt

    def update(self, screen: pygame.Surface, score: Any) -> None:
        """Change the value and resize the texts.

        Args:
            screen: Window surface.
            score: Value to show.
        """
        self.l_score[0].update(screen)
        self.l_score[1].txt = self.fmt.format(score)
        self.l_score[1].update(screen)

    def enter(self) -> None:
        """Build the texts."""
        if len(self.l_score) != 0:
            return
        gx, _ = self.para.grid_size
        mt, _ = self.para.vertical_margin
        _, mr = self.para.side_margin
        self.l_score.append(Grid_txt(self.title, (gx - mr / 2, mt + self.row),
                                     self.para, 2.25))
        self.l_score.append(Grid_txt("0", (gx - mr / 2, mt + self.row + 3),
                                     self.para, 1.5))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the texts.

        Args:
            screen: Window surface.
        """
        for line in self.l_score:
            line.draw(screen)


class Button:
    """A button with a normal and a pushed image."""

    def __init__(self, sprite: list[pygame.Surface], pos: tuple[float, float],
                 para: Parameter, size: tuple[float, float]) -> None:
        """Create the button.

        Args:
            sprite: ``[normal, pushed]`` images.
            pos: Top left corner on the grid.
            para: Shared parameters.
            size: Size in tiles.
        """
        self.sprite = sprite
        self.grid_size = size
        self.grid_pos = pos
        self.para = para
        self.continuede = False
        self.pushed = False
        self.time = 0.0
        self.idx = 0
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Animate and resize the button.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        if self.pushed and self.idx == 1:
            self.time += dt

        if self.time >= 0.1:
            self.continuede = True
        wid, hei = self.para.grid_size
        ox, oy, step = grid(screen, wid, hei)
        gx, gy = self.grid_pos

        pos = (ox + gx * step, oy + gy * step)
        img = self.sprite[self.idx]
        s_w, s_h = self.grid_size
        size = (round(s_w * step), round(s_h * step))
        img = pygame.transform.scale(img, size)
        self.image = img
        self.rect = img.get_rect(topleft=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the button.

        Args:
            screen: Window surface.
        """
        if self.image is not None and self.rect is not None:
            screen.blit(self.image, self.rect)


class Tchat:
    """A one line text input (cheat console and player name)."""

    def __init__(self, m_len: int, para: Parameter, pos: tuple[float, float],
                 size: tuple[float, float]) -> None:
        """Create the input.

        Args:
            m_len: Max number of characters.
            para: Shared parameters.
            pos: Top left corner on the grid.
            size: Size in tiles.
        """
        self.para = para

        self.max_len = m_len
        self.grid_pos = pos
        self.final_pos: tuple[float, float] = pos
        self.size = size

        self.cursor = 0
        self.count = 0.0

        self.print = False
        self.allowed: Callable[[str], bool] | None = None

        self.screen_size: tuple[int, int] | None = None
        self.txt: Grid_txt | None = None
        self.select_txt: Grid_txt | None = None
        self.bg: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Edit the text with the keyboard.

        Args:
            event: Pygame event.

        Returns:
            The text when ENTER is pushed, else ``None``.
        """
        if not self.print or event.type != pygame.KEYDOWN or self.txt is None:
            return None
        text = self.txt.txt
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.txt.txt = ""
            self.cursor = 0
            return text
        if event.key == pygame.K_ESCAPE:
            self.print = False
        elif event.key == pygame.K_BACKSPACE:
            if self.cursor > 0:
                self.txt.txt = text[:self.cursor - 1] + text[self.cursor:]
                self.cursor -= 1
        elif event.key == pygame.K_DELETE:
            self.txt.txt = text[:self.cursor] + text[self.cursor + 1:]
        elif event.key == pygame.K_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif event.key == pygame.K_RIGHT:
            self.cursor = min(len(text), self.cursor + 1)
        elif event.unicode and event.unicode.isprintable() \
                and len(text) < self.max_len:
            if self.allowed is not None and not self.allowed(event.unicode):
                return None
            self.txt.txt = text[:self.cursor] + event.unicode \
                + text[self.cursor:]
            self.cursor += 1
        return None

    def update(self, dt: float, screen: pygame.Surface) -> None:
        """Blink the cursor and resize the input.

        Args:
            dt: Time since the last frame (s).
            screen: Window surface.
        """
        if not self.print or self.txt is None or self.select_txt is None:
            return

        self.count += dt
        if self.count >= 0.5:
            self.count = 0

        self.txt.update(screen)
        self.select_txt.update(screen)

        if screen.get_size() != self.screen_size:
            self.screen_size = screen.get_size()
            gw, gh = self.para.grid_size
            ox, oy, step = grid(screen, gw, gh)
            gx, gy = self.grid_pos
            wid, hei = self.size
            self.final_pos = (round(ox + gx * step), round(oy + gy * step))
            self.bg = pygame.Surface((round(wid * step), round(hei * step)),
                                     pygame.SRCALPHA)
            self.bg.fill((0, 0, 0, 128))
            self.rect = self.bg.get_rect(topleft=self.final_pos)

        if self.txt._font is not None and self.txt.rect is not None \
                and self.select_txt.rect is not None:
            width = self.txt._font.size(self.txt.txt[:self.cursor])[0]
            self.select_txt.rect.left = self.txt.rect.left + width

    def enter(self) -> None:
        """Build the texts."""
        gx, gy = self.grid_pos
        _, hei = self.size
        pos = (gx + 0.3, gy + hei / 2)
        self.txt = Grid_txt("", pos, self.para, 1.2)
        self.txt.anchor = "midleft"
        self.txt.max_len = self.max_len
        self.select_txt = Grid_txt("|", pos, self.para, 1.2)
        self.select_txt.anchor = "midleft"
        self.cursor = 0
        self.count = 0
        self.screen_size = None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the input.

        Args:
            screen: Window surface.
        """
        if not self.print or self.bg is None or self.txt is None \
                or self.select_txt is None:
            return
        screen.blit(self.bg, self.final_pos)
        self.txt.draw(screen)
        if self.count <= 0.25:
            self.select_txt.draw(screen)


class Disp:
    """A plain rectangle placed on the grid."""

    def __init__(self, pos: tuple[float, float], size: tuple[float, float],
                 para: Parameter,
                 color: tuple[int, int, int, int] = (0, 0, 0, 255)) -> None:
        """Create the rectangle.

        Args:
            pos: Center on the grid.
            size: Size in tiles.
            para: Shared parameters.
            color: RGBA color.
        """
        self.para = para
        self.size = size
        self.grid_pos = pos
        self.color = color

        self.bg: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self.screen_size: tuple[int, int] | None = None

    def update(self, screen: pygame.Surface) -> None:
        """Resize the rectangle.

        Args:
            screen: Window surface.
        """
        if screen.get_size() == self.screen_size:
            return

        self.screen_size = screen.get_size()
        gw, gh = self.para.grid_size
        ox, oy, step = grid(screen, gw, gh)
        gx, gy = self.grid_pos
        wid, hei = self.size
        pos = (ox + gx * step, oy + gy * step)
        size = (round(wid * step), round(hei * step))
        self.bg = pygame.Surface(size, pygame.SRCALPHA)
        self.bg.fill(self.color)
        self.rect = self.bg.get_rect(center=pos)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the rectangle.

        Args:
            screen: Window surface.
        """
        if self.bg is not None and self.rect is not None:
            screen.blit(self.bg, self.rect)


class Help:
    """A window listing lines of text (cheat help)."""

    def __init__(self, pos: tuple[float, float], size: tuple[float, float],
                 para: Parameter, lines: list[str] | None = None) -> None:
        """Create the window.

        Args:
            pos: Center on the grid.
            size: Size in tiles.
            para: Shared parameters.
            lines: Lines to show (default: the cheat commands).
        """
        self.para = para
        self.grid_pos = pos
        self.grid_size = size
        self.lines = lines if lines is not None else CHEAT_HELP

        self.bg: Disp | None = None

        self.commandes: list[Grid_txt] = []

        self.print = False

    def update(self, screen: pygame.Surface) -> None:
        """Resize the window.

        Args:
            screen: Window surface.
        """
        if not self.print or self.bg is None:
            return
        self.bg.update(screen)
        for commande in self.commandes:
            commande.update(screen)

    def enter(self) -> None:
        """Build the texts."""
        self.bg = Disp(self.grid_pos, self.grid_size, self.para,
                       (15, 15, 15, 255))
        gx, gy = self.grid_pos
        dgw, dgh = self.grid_size
        self.commandes = []
        step = min(3.0, (dgh - 2) / max(1, len(self.lines)))
        for i, commande_name in enumerate(self.lines):
            pos = (gx - dgw / 2 + 1.5, gy - dgh / 2 + 2 + i * step)
            txt = Grid_txt(commande_name, pos, self.para, 1.1)
            txt.anchor = "midleft"
            self.commandes.append(txt)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the window.

        Args:
            screen: Window surface.
        """
        if not self.print or self.bg is None:
            return
        self.bg.draw(screen)
        for commande in self.commandes:
            commande.draw(screen)
