# Acceptance test plan

| # | Feature | Test | Expected | Result |
| - | --- | --- | --- | --- |
| 1 | Arguments | no arg / 2 args | usage message, exit 1 | OK |
| 2 | Config file | missing file, `.txt`, directory, invalid JSON, JSON array | clear error, no traceback | OK |
| 3 | Config values | wrong types, out of range, unknown keys, < 10 levels | warnings, defaults / clamp, game starts | OK |
| 4 | Comments | `#`, `//`, `/* */` in config.json | ignored | OK |
| 5 | Maze | sizes 8×8, 18×18, 30×30, 10×25 | maze centred, 4 ghosts, 4 super-pacgums | OK |
| 6 | Level 1 seed | start twice | same first maze | OK |
| 7 | Player | arrows / WASD / ZQSD | moves in corridors only | OK |
| 8 | Lives | touched by a ghost | -1 life, respawn in the middle | OK |
| 9 | Super-pacgum | eat one | +50, ghosts blue and fleeing for 7 s | OK |
| 10 | Eat ghost | touch a blue ghost | +200, ghost hidden, back in its corner after 5 s | OK |
| 11 | Timer | wait 90 s | -1 life, timer restarts | OK |
| 12 | Levels | finish / skip 10 levels | victory screen | OK |
| 13 | Game over | lose every life | game over screen with score | OK |
| 14 | Name entry | `bad!`, empty, 11+ chars, `Enzo 42` | invalid chars ignored, error if empty, saved | OK |
| 15 | Highscores | 11+ games | only top 10 kept, best first | OK |
| 16 | Corrupted highscore file | invalid JSON / entries | empty board or invalid entries skipped | OK |
| 17 | Pause | ESC, click "resume", MENU, QUIT | works, countdown after resume | OK |
| 18 | Cheats | every command of `/help` | effect applied | OK |
| 19 | Resize | resize window during each screen | everything rescaled | OK |
| 20 | Lint | `make lint`, `make lint-strict` | no error | OK |
| 21 | Package | `make package`, run `play.sh` | game starts from the zip | OK (macOS) |

## Bugs found / fixed

| Bug | Fix |
| --- | --- |
| `SUPER_PACGUM` undefined → crash when generating a level | constant added (`-6`) |
| Only 1 ghost created out of 4 | ghost values -2..-5 all handled |
| Pause animation crashed (list given instead of an image) | first frame of the animation used |
| Pause pacgums never came back | timer logic of `Pac_gum.update` fixed |
| Highscore sort crashed when a score was lower than every other | sorting moved to `load_scores` |
| `exit()` on missing image | clear message + `sys.exit(1)` |
