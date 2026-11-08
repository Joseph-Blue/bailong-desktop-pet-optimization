"""Offline ZIP tests; no application dependencies or real build required."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_windows


class WindowsPackageTests(unittest.TestCase):
    def test_archive_contains_complete_directory_and_matching_checksum(self):
        with tempfile.TemporaryDirectory(prefix='.build-zip-test-', dir=Path(__file__).resolve().parents[1]) as folder:
            root = Path(folder)
            output = root / 'build-vtest' / 'BailongPet'
            resources = ['BailongPet.exe', '_internal/python313.dll', 'tools/ffmpeg.exe',
                         'outputs/白龙桌宠素材/素材清单.json', 'app/sounds/click.wav',
                         'BUILD_INFO.json']
            for name in resources:
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode('utf-8'))
            (root / 'private.txt').write_text('outside the build', encoding='utf-8')
            with patch.object(build_windows.platform, 'machine', return_value='AMD64'):
                archive = build_windows.archive_build(output)
            self.assertEqual(archive.parent, root)
            self.assertTrue(archive.name.endswith('-windows-x64.zip'))
            with zipfile.ZipFile(archive) as bundle:
                files = {info.filename for info in bundle.infolist() if not info.is_dir()}
                self.assertEqual(files, {'BailongPet/' + name for name in resources})
                for name in resources:
                    self.assertEqual(bundle.read('BailongPet/' + name), name.encode('utf-8'))
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(archive.with_suffix('.zip.sha256').read_text(encoding='utf-8'),
                             f'{expected}  {archive.name}\n')

    def test_archive_only_after_successful_build(self):
        with patch.object(build_windows, 'build_desktop', side_effect=RuntimeError('failed')):
            with patch.object(build_windows, 'archive_build') as archive:
                with self.assertRaises(RuntimeError):
                    build_windows.main(['--zip'])
                archive.assert_not_called()

    def test_zip_option_uses_fresh_build_result(self):
        output = Path('fresh-build/BailongPet')
        with patch.object(build_windows, 'build_desktop', return_value=output) as build:
            with patch.object(build_windows, 'archive_build') as archive:
                build_windows.main(['--ffmpeg', 'custom.exe', '--zip'])
                build.assert_called_once_with('windows', ffmpeg_arg='custom.exe')
                archive.assert_called_once_with(output)


if __name__ == '__main__':
    unittest.main()
