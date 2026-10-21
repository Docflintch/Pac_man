#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   __main__.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/07/30 04:59:32 by enchueco              #+#    #+#          #
#   Updated: 2026/07/30 04:59:32 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

"""Main loop of the game: switch between the screens."""

from __future__ import annotations

import os
import sys
from typing import Any

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame  # noqa: E402

from src.tools import init_pygame  # noqa: E402
from src.screen import Screen, Menu, Game, Score, Game_over  # noqa: E402
from src.panel_admin import Parameter  # noqa: E402
from src.config import load_config, ConfigError  # noqa: E402


def main(conf: dict[str, Any] | None = None) -> None:
    """Open the window and run the screens until the player quits.

    Args:
        conf: Result of ``load_config`` (``None`` = default values).
    """
    disp = init_pygame()
    clock = pygame.time.Clock()

    para = Parameter(conf)
    screen: Screen = Menu(para)
    screen.enter()
    running = True

    while running:
        dt = min(clock.tick(60) / 1000, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                w, h = max(event.w, 320), max(event.h, 240)
                if (w, h) != (event.w, event.h):
                    disp = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            if screen.handle_event(event):
                running = False
        if not running:
            break

        name, ready = screen.moov_screen
        if ready:
            if name == "exit":
                break
            screen.moov_screen = ["", False]
            screen.exit()
            if name != "re":
                screen = get_screen(name, para)
            screen.enter()

        screen.update(dt, disp)
        disp.fill((0, 0, 0))
        screen.draw(disp)
        pygame.display.flip()
    pygame.quit()


def get_screen(name: str, para: Parameter) -> Screen:
    """Create the screen called ``name``.

    Args:
        name: ``"play"``, ``"Game_over"``, ``"menu"`` or ``"score"``.
        para: Shared parameters.

    Returns:
        The new screen (the menu for an unknown name).
    """
    if name == "play":
        return Game(para)
    elif name == "Game_over":
        return Game_over(para)
    elif name == "score":
        return Score(para)
    return Menu(para)


def run(argv: list[str]) -> int:
    """Check the arguments, load the config and start the game.

    Args:
        argv: Command line arguments (without the program name).

    Returns:
        The exit status.
    """
    if len(argv) != 1:
        print("usage: python3 pac-man.py <config.json>", file=sys.stderr)
        return 1
    try:
        conf = load_config(argv[0])
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    try:
        main(conf)
    except KeyboardInterrupt:
        pygame.quit()
    except pygame.error as exc:
        print(f"Error: pygame: {exc}", file=sys.stderr)
        pygame.quit()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
