1. Клиент
2. Создать исполняемого клиента: pyinstaller client_ws.py
3. Параметры запуска: --url - адрес сервера, --port - порт сервера, --samplerate, --channels, --dtype 
4. Сервер
5. Создать докер образ сервера: docker build --tag {dockerhub_yser_name}/{app_name}:{version} .
6. Параметры сервера (ENV): FORMAT, DURATION, SAMPLERATE, ...
