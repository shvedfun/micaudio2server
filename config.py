from pydantic import BaseModel
import sounddevice as sd


def get_microphonedevices(device=None, kind=None):
    devices = sd.query_devices(device=device, kind=kind)
    return devices


class DeviceStream(BaseModel):
    device: dict
    samplerate: int = 8000
    channels: int = 1
    dtype: str = 'int16'


mic_config = DeviceStream(device=get_microphonedevices(kind='input'))
