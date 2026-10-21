# Blocking points

| Problem | Impact | Solution |
| --- | --- | --- |
| The maze package gives wall masks per cell, the game needs tiles | characters could not move on cells | conversion 1 cell → 2×2 tiles, wall sprite chosen from neighbours |
| "42" closed cells in the middle of the maze | unreachable zone full of walls | only the outline of the zone is kept, pacgums only on reachable tiles |
| Responsive layout | positions broke when resizing | every object uses grid units + `tools.grid` |
| Packaged build launched without argument (double click) | usage error | `play.sh` / `play.bat` launchers pass `config.json` |
| TODO | | |
