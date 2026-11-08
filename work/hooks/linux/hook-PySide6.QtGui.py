"""Drop unused PDF and virtual-keyboard plugin dependency trees on Linux."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
excluded_plugins = {'libqpdf.so', 'libqtvirtualkeyboardplugin.so'}
binaries = [(source, destination) for source, destination in binaries
            if Path(source).name not in excluded_plugins]
