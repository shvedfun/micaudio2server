import sys
import time
import traceback
from argparse import ArgumentParser
import asyncio
import datetime
import logging
import struct

import sounddevice as sd
import websockets
from config import DeviceConfig, get_microphonedevices, log_format

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


class Microphone:

    def __init__(self, mic_config: DeviceConfig, url='ws://localhost', port=7654):
        self.device = get_microphonedevices()
        self.mic: DeviceConfig = mic_config # TODO kind='input'
        self.server_url = url + ':' + str(port)
        self.max_file_size = 0
        self.buffer: bytes = bytes([])
        self.len_chunk = 4000 * 2
        self.stream: sd.RawInputStream = None

    async def run_microphone(self):
        async for indata, frame_count, time_info, status in self.mic_stream_generator(
                channels=self.mic.channels, device=self.device['index'],
                samplerate=self.mic.samplerate, dtype=self.mic.dtype
        ):
            logger.info(f'status = {status} frame_count {frame_count} ')

    async def mic_stream_generator(self, channels=1, **kwargs):
        q_in = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def callback(in_data, frame_count, time_info, status):
            if len(in_data) > 0:
                loop.call_soon_threadsafe(q_in.put_nowait, (in_data, frame_count, time_info, status))

        def finished_callback():
            logger.warning(f'Что-то пошло не так. Проверьте подключение микрофона. Остановите и перезапустите программу')

        self.stream = sd.RawInputStream(
            callback=callback, channels=channels,
            finished_callback=finished_callback, **kwargs
        )
        with self.stream:
            while True:
                indata, frame_count, time_info, status = await q_in.get()
                yield indata, frame_count, time_info, status

    async def send2ws(self):
        while True:
            i = 0
            async with websockets.connect(self.server_url) as ws:
                async for indata, frame_count, time_info, status in self.mic_stream_generator(
                        channels=self.mic.channels, device=self.device['index'],
                        samplerate=self.mic.samplerate, dtype=self.mic.dtype
                ):
                    indata = bytes(indata)
                    self.buffer += indata
                    if len(self.buffer) >= self.len_chunk:
                        tst = datetime.datetime.utcnow().timestamp()
                        btst = struct.pack('d', tst)
                        indata = bytes(btst) + self.buffer[:self.len_chunk]
                        if i % 20 == 0:
                            logger.info(f'status = {status} frame_count {frame_count} ')
                        await ws.send(indata)
                        self.buffer = self.buffer[self.len_chunk:]
                        i += 1


async def main():
    mic_config = DeviceConfig()
    parser = ArgumentParser()
    parser.add_argument('--samplerate', type=int, help='audio samplerate', required=False)
    parser.add_argument('--channels', type=int, help='audio channels', required=False)
    parser.add_argument('--url', type=str, help='server url', required=False)
    parser.add_argument('--port', type=int, help='server port', required=False)
    args = parser.parse_args()
    if args.samplerate:
        mic_config.samplerate = args.samplerate
        logger.info(f'samplerate = {args.samplerate}')
    if args.channels:
        mic_config.channels = args.channels
    logger.info(f'mic_config = {mic_config}')
    server_params = {}
    if args.url:
        server_params['url'] = args.url
    if args.port:
        server_params['port'] = args.port
    while True:
        try:
            mic = Microphone(mic_config=mic_config, **server_params)
            await mic.send2ws()
        except Exception as e:
            logger.critical(f' {e}')
            await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
