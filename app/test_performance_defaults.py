import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QDialogButtonBox
from pet import Pet
from performance_preferences import read_performance_preferences, decode_size
from performance_settings import PerformanceSettings

app = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parents[1]


class PerformanceDefaultsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='.build-preferences-test-', dir=ROOT)
        self.addCleanup(self.folder.cleanup)
        self.path = str(Path(self.folder.name) / 'settings.ini')
        self.settings = QSettings(self.path, QSettings.Format.IniFormat)

    def test_new_install_is_512_and_12_independent_of_dpi(self):
        resolution, capacity, fps, preload = read_performance_preferences(self.settings)
        self.assertEqual((resolution, capacity, fps, preload), (512, 12, 'full', False))
        for dpi in (1, 1.25, 1.5, 2, 3):
            self.assertEqual(decode_size(resolution, dpi), 512)

    def test_existing_preferences_survive_reload_including_auto(self):
        for resolution, capacity, fps in ((720, 60, 'full'), (0, 24, '20'), (256, 6, '15')):
            self.settings.setValue('animationResolution', resolution)
            self.settings.setValue('animationBufferFrames', capacity)
            self.settings.setValue('animationFPSLimit', fps)
            self.settings.sync()
            reloaded = QSettings(self.path, QSettings.Format.IniFormat)
            self.assertEqual(read_performance_preferences(reloaded), (resolution, capacity, fps, False))

    def test_invalid_values_fall_back_to_shared_defaults(self):
        for resolution, capacity in (('broken', 'broken'), (999, 0), (-1, 241)):
            self.settings.setValue('animationResolution', resolution)
            self.settings.setValue('animationBufferFrames', capacity)
            self.settings.setValue('animationFPSLimit', 'invalid')
            self.assertEqual(read_performance_preferences(self.settings), (512, 12, 'full', False))

    def test_startup_dialog_apply_and_reset_use_same_preferences(self):
        with patch('pet.QSettings', return_value=self.settings), patch.object(Pet, 'play'):
            pet = Pet()
            dialog = PerformanceSettings(pet)
            try:
                self.assertEqual((pet.resolution, pet.buffer_capacity, pet.frame_size), (512, 12, 512))
                self.assertEqual((dialog.quality.currentData(), dialog.capacity_value()), (512, 12))
                dialog.quality.setCurrentIndex(dialog.quality.findData(720))
                dialog.capacity.setText('36')
                dialog.fps.setCurrentIndex(dialog.fps.findData('20'))
                dialog.preload.setChecked(True)
                self.assertFalse(dialog.capacity.isEnabled())
                self.assertFalse(dialog.buffer_slider.isEnabled())
                dialog.apply()
                self.assertEqual(read_performance_preferences(self.settings), (720, 36, '20', True))
                dialog.preload.setChecked(False)
                self.assertEqual(dialog.capacity.text(), '36')
                self.assertTrue(dialog.buffer_slider.isEnabled())
                dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.RestoreDefaults).click()
                self.assertTrue(dialog.apply_button.isEnabled())
                dialog.apply()
                self.assertEqual((pet.frame_size, pet.buffer_capacity), (512, 12))
                self.settings.sync()
                self.assertEqual(read_performance_preferences(QSettings(self.path, QSettings.Format.IniFormat)), (512, 12, 'full', False))
            finally:
                dialog.close()
                pet.close()

    def test_buffer_input_validation_and_slider_stay_in_sync(self):
        with patch('pet.QSettings', return_value=self.settings), patch.object(Pet, 'play'):
            pet = Pet()
            dialog = PerformanceSettings(pet)
            try:
                for text in ('', 'invalid', '0', '241', '12.5'):
                    dialog.capacity.setText(text)
                    dialog.commit_capacity()
                    self.assertEqual(dialog.capacity.text(), '12')
                    self.assertEqual(dialog.buffer_slider.value(), 12)
                dialog.capacity.setText(' 240 ')
                dialog.commit_capacity()
                self.assertEqual(dialog.buffer_slider.value(), 240)
                dialog.buffer_slider.setValue(6)
                self.assertEqual(dialog.capacity.text(), '6')
            finally:
                dialog.close()
                pet.close()


if __name__ == '__main__':
    unittest.main()
