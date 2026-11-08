from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from frame_buffer import FrameBuffer
from video_frames import rgba_frames

ROOT = Path(__file__).resolve().parents[1]
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except (ImportError, RuntimeError):
    FFMPEG = None


@unittest.skipUnless(FFMPEG, 'Requires the existing build FFmpeg')
class WebMFrameRateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(prefix='.build-rate-test-', dir=ROOT)
        cls.addClassCleanup(cls.folder.cleanup)
        cls.paths = {}
        for rate in (10, 24, 30):
            path = Path(cls.folder.name) / f'{rate}.webm'
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
            subprocess.run([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i',
                            f'color=c=red@0.5:s=16x16:r={rate}:d=1,format=yuva420p',
                            '-c:v', 'libvpx-vp9', '-auto-alt-ref', '0', str(path)],
                           check=True, capture_output=True, timeout=30, **kwargs)
            cls.paths[rate] = path

    def test_full_and_capped_rates_preserve_duration_and_alpha(self):
        for native, path in self.paths.items():
            for cap in (None, 20, 15):
                with self.subTest(native=native, cap=cap):
                    rates = []
                    with patch('video_frames.ffmpeg_path', return_value=FFMPEG):
                        frames = list(rgba_frames(path, 8, rate_changed=rates.append, fps=cap))
                    expected = native if cap is None else min(native, cap)
                    self.assertEqual(rates, [expected])
                    self.assertEqual(len(frames), expected)
                    self.assertEqual(len(frames[0]), 8*8*4)
                    self.assertTrue(all(0 < alpha < 255 for alpha in frames[0][3::4]))


class WebPFrameRateTests(unittest.TestCase):
    def test_cap_resamples_frames_without_changing_duration(self):
        with tempfile.TemporaryDirectory(prefix='.build-webp-test-', dir=ROOT) as folder:
            path = Path(folder) / 'clip.webp'
            frames = [Image.new('RGBA', (2, 2), (index*8, 0, 0, 128)) for index in range(30)]
            frames[0].save(path, save_all=True, append_images=frames[1:], duration=33, lossless=True)
            buffer = FrameBuffer()
            try:
                for cap, expected in ((None, 30), (20, 20), (15, 15)):
                    decoded = list(buffer.decode(buffer.generation, path, 2, 1, cap))
                    self.assertEqual(len(decoded), expected)
                    self.assertEqual(buffer.rate, expected)
            finally:
                buffer.close()


if __name__ == '__main__':
    unittest.main()
