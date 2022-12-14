FROM python:3.11.0

RUN apt-get -y update
RUN apt-get install -y ffmpeg

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r req.txt