#
FROM python:3.12.3-bookworm

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install libportaudio2 -y

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#VOLUME /usr/src/app/audio

EXPOSE 7654

CMD [ "python", "./server_ws.py" ]