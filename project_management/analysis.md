# Analysis and choices

## Needs (from the subject)
Playable Pac-Man, JSON config with comments, A-Maze-ing package as-is,
persistent top 10, menu / game / pause / game over / victory, cheat mode,
packaging on a public platform, flake8 + mypy, no traceback.

## Choices

| Topic | Choice | Why |
| --- | --- | --- |
| Graphic library | pygame (subset with MLX equivalents) | portable, simple, packages well with PyInstaller |
| Layout | everything in grid units scaled to the window | resizable window without special cases |
| Screens | one class per screen + `moov_screen` request | simple state machine, each screen independent |
| Next level | same `Game` object re-entered (`"re"`) | score and lives are kept for free |
| Maze | 1 cell → 2×2 tiles | walls become tiles the characters can't enter, simple tile movement |
| Ghost AI | one shared BFS distance field + 4 profiles | cheap (one BFS per Pac-Man tile), 4 distinct behaviours with one algorithm |
| Time out | lose a life, timer restarts | keeps the level, punishes without ending the game |
| Highscores | JSON next to the config file | readable, no dependency, writable in the packaged build |
| Cheats | console in the menu | many options without reserving keys during the game |
| Packaging | PyInstaller one-folder + launchers | the game always receives its config argument |
