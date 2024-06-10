1. Клиент
2. Создать исполняемого клиента: pyinstaller client_ws.py
3. Параметры запуска: --url - адрес сервера, --port - порт сервера, --samplerate, --channels, --dtype 
4. Сервер
5. Создать докер образ сервера: docker build --tag {dockerhub_yser_name}/{app_name}:{version} .
6. Параметры сервера (ENV): FORMAT, DURATION, SAMPLERATE, ...

Создать контейнер:
docker container create|run -p 7654:7654 --name horeca-test-audio-capture-2 -v /home/maksim/horeca/apps/test-audio-capture/input:/usr/src/app/audio shvedfun/server_ws:v0.20

help
- sudo ln -s /etc/nginx/sites-available/horecaudio /etc/nginx/sites-enabled/horecaudio

- docker container create -p 7654:7654 --name horeca-test-audio -v /home/victor/horeca/audio:/usr/src/app/audio cr.yandex/crp23u17la71rbk47bcs/server_ws:0.20

- docker pull cr.yandex/crp23u17la71rbk47bcs/server_ws:0.20

- yc container registry configure-docker

docker container create -p 7654:7654 --name horeca-test-audio-44100 -e SAMPLERATE=44100 -v /home/victor/horeca/audio:/usr/src/app/audio cr.yandex/crp23u17la71rbk47bcs/server_ws:0.20