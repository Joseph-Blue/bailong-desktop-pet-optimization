"""Use the upstream Qt hook, excluding two unused plugin dependency trees.

Filter before PyInstaller analyzes plugin DLLs, so their Qt PDF and virtual
keyboard/QML/Quick dependencies are not collected solely for these plugins.
Keep native platform input contexts, image formats, styles and render backends.
"""
from pathlib import Path

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
excluded_plugins = {'qpdf.dll', 'qtvirtualkeyboardplugin.dll'}
binaries = [(source, destination) for source, destination in binaries
            if Path(source).name.lower() not in excluded_plugins]
