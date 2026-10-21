PYTHON		?= python3
PIP			?= $(PYTHON) -m pip
CONFIG		?= config.json
# A-Maze-ing package given to the project (installed as-is)
MAZE_PKG	?= mazegenerator-2.1.0-py3-none-any.whl

MYPY_FLAGS	= --warn-return-any --warn-unused-ignores --ignore-missing-imports \
			  --disallow-untyped-defs --check-untyped-defs

all: run

install:
	$(PIP) install -r requirements.txt
	@if [ -f "$(MAZE_PKG)" ]; then \
		$(PIP) install --force-reinstall "$(MAZE_PKG)"; \
	elif $(PYTHON) -c "import mazegenerator" 2>/dev/null; then \
		echo "mazegenerator already installed"; \
	else \
		echo "Error: put the A-Maze-ing package at ./$(MAZE_PKG)"; exit 1; \
	fi

run:
	$(PYTHON) pac-man.py $(CONFIG)

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache \) -prune -exec rm -rf {} +
	rm -rf build dist

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

# build the itch.io package: dist/pac-man-<os>.zip
package:
	$(PIP) install -r requirements-build.txt
	$(PYTHON) -m PyInstaller --noconfirm --clean pacman.spec
	cp config.json INSTRUCTIONS.txt packaging/play.sh packaging/play.bat dist/pac-man/
	cd dist && rm -f pac-man-$$(uname -s).zip && zip -qr pac-man-$$(uname -s).zip pac-man
	@echo "-> dist/pac-man-$$(uname -s).zip"

.PHONY: all install run debug clean lint lint-strict package
