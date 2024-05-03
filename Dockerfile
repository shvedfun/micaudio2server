#
FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#VOLUME /usr/src/app/tmp

EXPOSE 7654

CMD [ "python", "./server_ws.py" ]