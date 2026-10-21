#!/bin/sh
# Launch the game with the config file shipped next to it.
cd "$(dirname "$0")" && ./pac-man config.json
