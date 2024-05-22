import logging
import os
import sys
from argparse import ArgumentParser
import asyncio
import datetime
import struct

from websockets.server import serve as ws_server
import soundfile as sf

from config import DeviceConfig, log_format

log_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
formatter = logging.Formatter(
    fmt=log_format,
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


class AWServer:
    conv_dtype2len = {
        'int8': 1,
        'int16': 2,
        'int24': 3
    }
    format2file_params = {
        'raw': {'subtype': 'PCM_16', 'endian': 'LITTLE', 'format': 'RAW'},
        'ogg': {'subtype': 'OPUS', 'format': 'OGG'},
        'wav': {'subtype': 'PCM_16', 'endian': 'LITTLE', 'format': 'WAV'},
        'mp3': {'format': 'MP3'}
    }
    audio_folder_name = '/audio'

    def __init__(
            self, url: str = None, port: int = 7654, dtype: str = 'int16',
            channels: int = 1, samplerate: int = 8000, format: str='mp3', durations=100
    ):
        self._create_folder()
        self.adress: str = url
        self.channels: int = channels
        self.dtype: str = dtype
        self.file: sf.SoundFile = None
        self.port: int = port
        self.samplerate: int = int(samplerate)
        self.max_frames = self.samplerate * int(durations)
        self.buffer = bytes()
        self.len_frame = self._get_len_frame()
        self.format = format

    def _create_folder(self):
        cwd = os.getcwd()
        full_path = cwd + self.audio_folder_name
        logger.debug(f'full_path = {full_path}')
        if not os.path.isdir(full_path):
            os.mkdir(full_path)

    def __del__(self):
        if self.file:
            self.file.close()

    def _get_len_frame(self):
        assert self.dtype in self.conv_dtype2len.keys()
        return self.conv_dtype2len[self.dtype]

    async def run_server(self, callback=None) -> None:
        callback = callback or self.callback2file
        while True:
            try:
                async with ws_server(
                        ws_handler=callback, port=self.port #, host=self.adress
                ):
                    await asyncio.Future()
            except Exception as e:
                logger.critical(f'Error = {e}')
                if self.file:
                    self.file.close()

    async def callback2file(self, websocket):
        async for data in websocket:
            btst = data[:8]
            tst = struct.unpack('d', btst)[0]
            data = data[8:]
            end_tst = tst + float((len(data)//self.len_frame)/self.samplerate)
            self.buffer += data
            while (len(self.buffer) // self.len_frame) > self.max_frames:
                data = self.buffer[:self.max_frames * self.len_frame]
                start_tst = end_tst - float(len(self.buffer)//self.len_frame/self.len_frame)
                file = self._get_file(start_tst)
                logger.debug(f'write file = {file.name}')
                self.file.buffer_write(data, dtype=self.dtype)
                self.file.close()
                self.buffer = self.buffer[self.max_frames * self.len_frame:]

    def _get_file(self, tst: float=None):
        if self.file and not self.file.closed:
            return self.file
        if tst is None:
            tst = datetime.datetime.utcnow().timestamp()
        tst = int(tst)
        file = sf.SoundFile(
            f'audio/audio_{str(tst)}.' + self.format, mode='w', channels=self.channels,
            samplerate=self.samplerate, **self.format2file_params[self.format] #, subtype='PCM_16', endian='LITTLE', format='RAW'
        )
        self.file = file
        return self.file


def init_env(params):
    if os.getenv('SAMPLERATE'):
        params['samplerate'] = os.getenv('SAMPLERATE')
    if os.getenv('CHANNELS'):
        params['channels'] = os.getenv('CHANNELS')
    if os.getenv('FORMAT'):
        params['format'] = os.getenv('FORMAT')
    if os.getenv('DURATION'):
        params['duration'] = os.getenv('DURATION')
    return params


def init_args(params):
    parser = ArgumentParser()
    parser.add_argument('--samplerate', type=int, help='audio samplerate', required=False)
    parser.add_argument('--channels', type=int, help='audio channels', required=False)
    parser.add_argument('--format', type=str, help='format audiofile', required=False)
    parser.add_argument('--duration', type=int, help='duration audiofile in sec.', required=False)
    args = parser.parse_args()
    if args.samplerate:
        params['samplerate'] = int(args.samplerate)
    if args.channels:
        params['channels'] = int(args.channels)
    if args.format:
        params['format'] = args.format
    if args.duration:
        params['duration'] = int(args.duration)
    return params


if __name__ == '__main__':
    params = DeviceConfig().dict()
    params = init_env(params)
    params = init_args(params)
    logger.info(f'params = {params}')

    server = AWServer(**params)
    asyncio.run(server.run_server())
