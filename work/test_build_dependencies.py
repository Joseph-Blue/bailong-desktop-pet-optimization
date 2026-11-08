"""Check missing and mismatched packages without changing any installed environment."""
from importlib import metadata
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from check_build_dependencies import missing_dependencies, pinned_requirements, ROOT


class BuildDependencyTests(unittest.TestCase):
    def test_current_requirements_include_application_and_build_packages(self):
        packages = dict(pinned_requirements(ROOT / 'requirements-build.txt'))
        self.assertIn('PySide6', packages)
        self.assertIn('pyinstaller', packages)
        self.assertIn('imageio-ffmpeg', packages)

    def test_missing_mismatched_and_satisfied_packages(self):
        with tempfile.TemporaryDirectory(prefix='.build-deps-test-', dir=ROOT) as folder:
            path = Path(folder) / 'requirements.txt'
            path.write_text('missing==1.0\nwrong==2.0\nready==3.0\n', encoding='utf-8')

            def version(name):
                if name == 'missing':
                    raise metadata.PackageNotFoundError(name)
                return {'pip': '26.0', 'wrong': '1.0', 'ready': '3.0'}[name]

            with patch('check_build_dependencies.metadata.version', side_effect=version):
                missing = missing_dependencies(path)
            self.assertEqual(missing, ['missing==1.0（当前：未安装）', 'wrong==2.0（当前：1.0）'])

    def test_all_pinned_packages_satisfied(self):
        path = ROOT / 'requirements-build.txt'
        versions = dict(pinned_requirements(path), pip='26.0')
        with patch('check_build_dependencies.metadata.version', side_effect=versions.__getitem__):
            self.assertEqual(missing_dependencies(path), [])


if __name__ == '__main__':
    unittest.main()
