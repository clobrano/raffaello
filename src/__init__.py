import os

_ROOT = os.path.abspath(os.path.dirname(__file__))
def get_preset_location(name):
    return os.path.join(_ROOT, 'presets', name)
