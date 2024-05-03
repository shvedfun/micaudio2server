import logging
from fastapi import FastAPI, WebSocket, BackgroundTasks
from log_config import LogConfig

app = FastAPI()

logging.config.dictConfig(LogConfig().dict())
logger = logging.getLogger("ws_server")

def process_data(data):
    print(f'получил len = {len(data)}')

@app.websocket('')
async def server(websocket: WebSocket): # , background_tasks: BackgroundTasks
    print(f'Зашел')
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # background_tasks.add_task(process_data, data)
        await websocket.send_text(f' Receive {data}')