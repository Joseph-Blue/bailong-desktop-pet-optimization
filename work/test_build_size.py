"""Offline packaging checks: no app build, dependency install or asset edits."""
from pathlib import Path
import os
import runpy
import tempfile
import unittest
import json
from unittest.mock import patch

from build_common import ROOT, place_ffmpeg
import build_common


class DecoderPlacementTests(unittest.TestCase):
    def test_windows_moves_decoder_and_preserves_other_files(self):
        with tempfile.TemporaryDirectory(prefix='.build-size-test-', dir=ROOT) as folder:
            root = Path(folder)
            source = root / '_internal/tools/ffmpeg-versioned.exe'
            source.parent.mkdir(parents=True)
            data = b'decoder bytes' * 100
            source.write_bytes(data)
            library = root / '_internal/runtime.dll'
            library.write_bytes(b'runtime')
            place_ffmpeg(root, 'windows', Path('ffmpeg-versioned.exe'))
            self.assertFalse(source.exists())
            self.assertEqual((root / 'tools/ffmpeg.exe').read_bytes(), data)
            self.assertEqual(library.read_bytes(), b'runtime')
            self.assertEqual(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
                             len(data) + len(b'runtime'))

    def test_posix_alias_points_to_collected_binary_without_copying(self):
        for target in ('linux', 'macos'):
            with self.subTest(target=target), tempfile.TemporaryDirectory(prefix='.build-size-test-', dir=ROOT) as folder:
                root = Path(folder)
                resources = root / 'Contents/Resources' if target == 'macos' else root
                source = (resources if target == 'macos' else root / '_internal') / 'tools/ffmpeg-versioned'
                source.parent.mkdir(parents=True)
                source.write_bytes(b'decoder')
                with patch.object(Path, 'symlink_to', autospec=True) as link:
                    place_ffmpeg(root, target, Path('ffmpeg-versioned'))
                alias = resources / 'tools/ffmpeg'
                link.assert_called_once_with(alias, os.path.relpath(source, alias.parent))
                self.assertEqual(source.read_bytes(), b'decoder')
                self.assertFalse(alias.exists())

    def test_macos_canonical_name_needs_no_alias(self):
        with tempfile.TemporaryDirectory(prefix='.build-size-test-', dir=ROOT) as folder:
            root = Path(folder)
            binary = root / 'Contents/Resources/tools/ffmpeg'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'decoder')
            with patch.object(Path, 'symlink_to') as link:
                place_ffmpeg(root, 'macos', Path('ffmpeg'))
            link.assert_not_called()
            self.assertEqual(binary.read_bytes(), b'decoder')


class QtHookTests(unittest.TestCase):
    def test_filters_optional_plugins_and_keeps_native_input_and_images(self):
        plugins = [('C:/Qt/plugins/' + name, 'PySide6/plugins') for name in (
            'imageformats/qpdf.dll', 'platforminputcontexts/qtvirtualkeyboardplugin.dll',
            'platforms/qwindows.dll', 'platforminputcontexts/native.dll', 'imageformats/qwebp.dll',
            'imageformats/qjpeg.dll', 'iconengines/qsvgicon.dll')]
        with patch('PyInstaller.utils.hooks.qt.add_qt6_dependencies',
                   return_value=(['PySide6.QtCore'], plugins, [('qt.qm', 'translations')])):
            hook = runpy.run_path(str(ROOT / 'work/hooks/windows/hook-PySide6.QtGui.py'))
        self.assertEqual(hook['binaries'], plugins[2:])
        self.assertEqual(hook['hiddenimports'], ['PySide6.QtCore'])
        self.assertEqual(hook['datas'], [('qt.qm', 'translations')])


class WindowsSlimBuildTests(unittest.TestCase):
    def test_build_wires_filters_and_outputs_one_decoder(self):
        with tempfile.TemporaryDirectory(prefix='.build-size-test-', dir=ROOT) as folder:
            root = Path(folder)
            source = Path('ffmpeg-versioned.exe')
            def collect(arguments):
                output = Path(arguments[arguments.index('--distpath') + 1]) / 'BailongPet'
                (output / '_internal/tools').mkdir(parents=True)
                (output / '_internal/tools' / source.name).write_bytes(b'decoder')
                (output / 'BailongPet.exe').write_bytes(b'application')
                (output / '_internal/runtime.dll').write_bytes(b'runtime')
            with patch.object(build_common, 'ROOT', root), \
                 patch.object(build_common.sys, 'platform', 'win32'), \
                 patch.object(build_common, 'check_python'), \
                 patch.object(build_common, 'build_inputs', return_value=(root, {}, set(), source)), \
                 patch.object(build_common, 'copy_resources'), \
                 patch('PyInstaller.__main__.run', side_effect=collect) as run:
                output = build_common.build_desktop('windows')
            args = run.call_args.args[0]
            self.assertEqual(args[args.index('--additional-hooks-dir') + 1], str(root / 'work/hooks/windows'))
            excluded = [args[index + 1] for index, value in enumerate(args) if value == '--exclude-module']
            self.assertEqual(set(excluded), {'PIL.AvifImagePlugin', 'PIL._avif'})
            self.assertEqual((output / 'tools/ffmpeg.exe').read_bytes(), b'decoder')
            self.assertFalse((output / '_internal/tools' / source.name).exists())
            self.assertEqual((output / '_internal/runtime.dll').read_bytes(), b'runtime')
            self.assertEqual(json.loads((output / 'BUILD_INFO.json').read_text())['platform'], 'windows')


if __name__ == '__main__':
    unittest.main()
