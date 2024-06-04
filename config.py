from pydantic import BaseModel
import sounddevice as sd


def get_microphonedevices(device=None, kind='input'):
    devices = sd.query_devices(device=device, kind=kind)
    if type(devices) is dict:
        return devices
    if len(devices) > 0:
        return devices[0]
    raise IOError


class DeviceConfig(BaseModel):
    samplerate: int = 8000
    channels: int = 1
    dtype: str = 'int16'


log_format = '%(asctime)s - %(module)s/%(funcName)s - %(levelname)s - %(message)s'
