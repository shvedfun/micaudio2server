from pydantic import BaseModel
import sounddevice as sd


def get_microphonedevices(device=None, kind=None):
    devices = sd.query_devices(device=device, kind=kind)
    return devices


class DeviceConfig(BaseModel):
    samplerate: int = 8000
    channels: int = 1
    dtype: str = 'int16'

log_format = '%(asctime)s - %(module)s/%(funcName)s - %(levelname)s - %(message)s'
