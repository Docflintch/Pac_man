# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: `make package` (or `pyinstaller pacman.spec`).
# Builds dist/pac-man/ (executable + sprites + font).

a = Analysis(
    ['pac-man.py'],
    pathex=['.'],
    datas=[('sprite', 'sprite'), ('font', 'font')],
    hiddenimports=['mazegenerator'],
    excludes=['tkinter'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pac-man',
    console=True,
)
coll = COLLECT(exe, a.binaries, a.datas, name='pac-man')
