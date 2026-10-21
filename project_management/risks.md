# Risk analysis

| Risk | Prob. | Impact | Mitigation |
| --- | --- | --- | --- |
| The assigned maze package has another interface / crashes | medium | high | adapter in `tools.convert_maze`, any exception → `MazeError`, 3 retries, back to menu |
| Package re-installed during the review | high | medium | never modified, installed from its wheel by `make install` |
| Config modified during the review (invalid values) | high | high | validation of every key, clamp + default + warning, unknown keys ignored |
| Traceback = project failed | medium | high | try/except around files, config, generator, pygame; tested with bad inputs |
| Highscore file corrupted / read-only | low | medium | invalid entries skipped, write errors → warning |
| Packaged game can't find assets / config | medium | high | resources resolved from the bundle folder, launchers pass `config.json` |
| Ghosts too hard / too easy | medium | low | speeds and timings in the config, profiles in `ghost_ai.py` |
| Small window / big maze unreadable | low | low | grid scaled to the window, maze area grows with the level size |
| Late delivery | medium | high | TODO: describe planning margin |
