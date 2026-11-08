"""Keep the upstream PySide6 hook, without the bundled software OpenGL DLL."""
from pathlib import Path
import runpy

import PyInstaller

upstream = runpy.run_path(str(Path(PyInstaller.__file__).parent / 'hooks/hook-PySide6.py'))
hiddenimports = upstream.get('hiddenimports', [])
datas = upstream.get('datas', [])
binaries = [(source, destination) for source, destination in upstream.get('binaries', [])
            if Path(source).name.lower() != 'opengl32sw.dll']
