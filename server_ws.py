from argparse import ArgumentParser
import asyncio
import datetime
import struct

from websockets.server import serve as ws_server
import soundfile as sf

from config import mic_config, DeviceStream

class AWServer:
    conv_dtype2len = {
        'int8': 1,
        'int16': 2,
        'int24': 3
    }
    format2file_params = {
        'raw': {'subtype': 'PCM_16', 'endian': 'LITTLE', 'format': 'RAW'},
        'ogg': {'subtype': 'OPUS', 'format': 'OGG'},
        'wav': {'subtype': 'PCM_16', 'endian': 'LITTLE', 'format': 'WAV'}
    }

    def __init__(
            self, url: str = None, port: int = 7654, dtype: str = 'int16',
            channels: int = 1, samplerate: int = 8000, format: str='ogg'
    ):
        self.adress: str = url
        self.channels: int = channels
        self.dtype: str = dtype
        self.file: sf.SoundFile = None
        self.port: int = port
        self.samplerate: int = samplerate
        self.max_frames = self.samplerate * 15
        self.buffer = bytes()
        self.len_frame = self._get_len_frame()
        self.format = format
        self.file = None

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
                print(f'Error = {e}')
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
                print(f'{datetime.datetime.fromtimestamp(tst)} len data = {len(data)}')
                data = self.buffer[:self.max_frames * self.len_frame]
                start_tst = end_tst - float(len(self.buffer)//self.len_frame/self.len_frame)
                self._get_file(start_tst)
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
            f'tmp/test_{str(tst)}.' + self.format, mode='w', channels=self.channels,
            samplerate=self.samplerate, **self.format2file_params[self.format] #, subtype='PCM_16', endian='LITTLE', format='RAW'
        )
        self.file = file
        return self.file


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--samplerate', type=int, help='audio samplerate', required=False)
    parser.add_argument('--channels', type=int, help='audio channels', required=False)
    parser.add_argument('--format', type=str, help='format audiofile', required=False)
    args = parser.parse_args()
    if args.samplerate:
        mic_config.samplerate = args.samplerate
        print(f'samplerate = {args.samplerate}')
    if args.channels:
        mic_config.channels = args.channels
    params = {'samplerate': mic_config.samplerate, 'dtype': mic_config.dtype, 'channels': mic_config.channels,}
    if args.format:
        params['format'] = args.format
    server = AWServer(**params)
    asyncio.run(server.run_server())
