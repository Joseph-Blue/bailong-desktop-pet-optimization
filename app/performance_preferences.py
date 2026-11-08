"""Shared performance defaults and validation for every desktop platform."""

DEFAULT_RESOLUTION = 512
DEFAULT_BUFFER_FRAMES = 12
DEFAULT_FPS_LIMIT = 'full'
FPS_LIMITS = ('full', '20', '15')
RESOLUTIONS = (0, 720, 512, 384, 256)
MIN_BUFFER_FRAMES = 6
MAX_BUFFER_FRAMES = 240


def read_performance_preferences(settings):
    def integer(key, default):
        try:
            return int(settings.value(key, default))
        except (TypeError, ValueError, OverflowError):
            return default

    resolution = integer('animationResolution', DEFAULT_RESOLUTION)
    if resolution not in RESOLUTIONS:
        resolution = DEFAULT_RESOLUTION
    capacity = integer('animationBufferFrames', DEFAULT_BUFFER_FRAMES)
    if not MIN_BUFFER_FRAMES <= capacity <= MAX_BUFFER_FRAMES:
        capacity = DEFAULT_BUFFER_FRAMES
    fps_limit = str(settings.value('animationFPSLimit', DEFAULT_FPS_LIMIT))
    if fps_limit not in FPS_LIMITS:
        fps_limit = DEFAULT_FPS_LIMIT
    preload = settings.value('preloadWholeAnimation', False, type=bool)
    return resolution, capacity, fps_limit, preload


def decode_size(resolution, device_pixel_ratio):
    return resolution or min(512, max(256, round(256 * device_pixel_ratio)))


def fps_cap(limit):
    return None if limit == 'full' else int(limit)
