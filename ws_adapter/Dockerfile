FROM python:3.13.2-slim

WORKDIR /usr/src/app

COPY . .

RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["./run_adapter.sh"]