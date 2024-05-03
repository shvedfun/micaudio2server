from argparse import ArgumentParser
import asyncio
import datetime
import logging
import struct

import sounddevice as sd
import websockets

from config import mic_config, DeviceStream

async def mic_stream_generator(channels=1, **kwargs):
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(in_data, frame_count, time_info, status):
        if len(in_data) > 0:
            loop.call_soon_threadsafe(q_in.put_nowait, (in_data, status))

    stream = sd.RawInputStream(callback=callback, channels=channels, **kwargs)
    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status


class Microthone:

    def __init__(self, mic_config: DeviceStream, url='ws://localhost', port=7654):
        self.mic: DeviceStream = mic_config # TODO kind='input'
        self.server_url = url + ':' + str(port)
        self.max_file_size = 0
        self.buffer: bytes = bytes([])
        self.len_chunk = 4000 * 2


    async def run_microfone(self):
        async for indata, status in mic_stream_generator(
                channels=self.mic.channels, device=self.mic.device['index'],
                samplerate=self.mic.samplerate, dtype=self.mic.dtype
        ):
            print(f'{datetime.datetime.utcnow()} status = {status} len {len(indata)}')

    async def send2ws(self):
        while True:
            try:
                async with websockets.connect(self.server_url) as ws:
                    async for indata, status in mic_stream_generator(
                            channels=self.mic.channels, device=self.mic.device['index'],
                            samplerate=self.mic.samplerate, dtype=self.mic.dtype
                    ):
                        indata = bytes(indata)
                        self.buffer += indata
                        if len(self.buffer) >= self.len_chunk:
                            tst = datetime.datetime.utcnow().timestamp()
                            btst = struct.pack('d', tst)
                            indata = bytes(btst) + self.buffer[:self.len_chunk]
                            print(f'{datetime.datetime.utcnow()} status = {status} len {len(indata)} type = {type(indata)}')
                            await ws.send(indata)
                            self.buffer = self.buffer[self.len_chunk:]
            except Exception as e:
                print(f'Error {e}')
                await asyncio.sleep(1)



async def main():
    parser = ArgumentParser()
    parser.add_argument('--samplerate', type=int, help='audio samplerate', required=False)
    parser.add_argument('--channels', type=int, help='audio channels', required=False)
    parser.add_argument('--url', type=str, help='server url', required=False)
    parser.add_argument('--port', type=int, help='server port', required=False)
    args = parser.parse_args()
    if args.samplerate:
        mic_config.samplerate = args.samplerate
        print(f'samplerate = {args.samplerate}')
    if args.channels:
        mic_config.channels = args.channels
    print(f'mic_config = {mic_config}')
    server_params = {}
    if args.url:
        server_params['url'] = args.url
    if args.port:
        server_params['port'] = args.port
    mic = Microthone(mic_config=mic_config, **server_params)
    await mic.send2ws()


if __name__ == '__main__':
    asyncio.run(main())