import logging
import os
import sys
from argparse import ArgumentParser
import asyncio
import datetime
import struct
from typing import Callable

from websockets.server import serve as ws_server
import soundfile as sf

from config import DeviceConfig
from utils import get_logger


log_level = logging.DEBUG
logger = get_logger(log_level)


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
            channels: int = 1, samplerate: int = 8000, format: str='mp3', duration=100
    ):
        self._create_folder()
        self.adress: str = url
        self.channels: int = channels
        self.dtype: str = dtype
        self.file: sf.SoundFile = None
        self.port: int = port
        self.samplerate: int = int(samplerate)
        self.max_frames = self.samplerate * int(duration)
        self.buffer = bytearray()
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

    async def run_server(self, callback: Callable = None) -> None:
        callback = callback or self.callback2file
        while True:
            try:
                async with ws_server(
                        ws_handler=callback, port=self.port
                ):
                    await asyncio.Future()
            except Exception as e:
                logger.critical(f'Error = {e}')
                if self.file:
                    self.file.close()
                await asyncio.sleep(2)

    async def callback2file(self, websocket):
        async for data in websocket:
            # вычисляю таймстемп блока данных
            btst = data[:8]
            tst = struct.unpack('d', btst)[0]
            self.buffer += data[8:]
            # Если  длина буфера достаточна, то скидываю в файл
            while (len(self.buffer) // self.len_frame) > self.max_frames:
                data = self.buffer[:self.max_frames * self.len_frame]
                file = self._save2file(data, tst)
                self.buffer = self.buffer[self.max_frames * self.len_frame:]

    def _save2file(self, data: bytearray, tst: float) -> None:
        """
        Записывает в файл буфер. В суффиксе имени файла указан таймстемп
        :data - буфер данных
        :param tst: таймстемп данных
        :return: None
        """
        if self.file and not self.file.closed:
            self.file.close()
        tst = int(tst)
        file = sf.SoundFile(
            f'audio/audio_{str(tst)}.' + self.format, mode='w', channels=self.channels,
            samplerate=self.samplerate, **self.format2file_params[self.format]
        )
        self.file = file
        self.file.buffer_write(data, dtype=self.dtype)
        self.file.close()
        logger.debug(f'write file = {file.name}')


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
