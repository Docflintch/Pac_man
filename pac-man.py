#!/usr/bin/env python3
# ########################################################################### #
#                                                                             #
#                                                          :::      ::::::::  #
#   pac-man.py                                           :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: enchueco <enchueco@student.42.fr>            +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/10/18 17:00:00 by enchueco              #+#    #+#          #
#   Updated: 2026/10/18 17:00:00 by enchueco             ###   ########.fr    #
#                                                                             #
# ########################################################################### #

"""Launcher: ``python3 pac-man.py config.json``."""

import os
import sys


def base_dir() -> str:
    """Give the folder holding ``sprite/`` and ``font/``.

    Returns:
        The PyInstaller bundle folder, or the folder of this file.
    """
    bundle = getattr(sys, "_MEIPASS", None)
    if isinstance(bundle, str):
        return bundle
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    args = [os.path.abspath(a) for a in sys.argv[1:]]
    os.chdir(base_dir())
    sys.path.insert(0, base_dir())
    from src.__main__ import run
    sys.exit(run(args))
