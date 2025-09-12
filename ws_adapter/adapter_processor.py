import asyncio
import json
import time
from base64 import b64encode
from datetime import datetime
from itertools import chain
from multiprocessing import Pool, Process, Queue
from os import getenv
from pathlib import Path

import cv2
import numpy as np
import websockets

MIN_VID_WIDTH_PX = 640
MIN_VID_HEIGHT_PX = 480
MIN_VID_LENGTH_SEC = 10  # error if less
MAX_VID_LENGTH_SEC = 20  # extra is dropped
MAX_FILE_TTL_SEC = 300
MAX_PROCESSING_TIME_SEC = 30
MONITORING_INTERVAL_SEC = 0.2
CLEANUP_INTERVAL_SEC = 60
NUM_WORKERS = 4


working_dir = Path(getenv("GIGADOC_ADAPTER_DIR", "/tmp/gigadoc_cache/"))
ws_server_ip = getenv("GIGADOC_WS_SERVER_IP", "127.0.0.1")
ws_server_port = getenv("GIGADOC_WS_SERVER_PORT", "9000")
ws_server = f"ws://{ws_server_ip}:{ws_server_port}"


input_dir = working_dir.joinpath("input")
output_dir = working_dir.joinpath("output")
input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)


def encode_frame(frame):
    return (b"base64," + b64encode(cv2.imencode(".png", frame)[1].tobytes())).decode("ascii")


def gen_error_result(error_code, error_text):
    return json.dumps(
        {
            "status": "fail",
            "error_code": error_code,
            "error_text": str(error_text),
        }
    )


def preprocess_video(video_filename):
    print(f"preprocess_video: {video_filename} start")
    video = cv2.VideoCapture(video_filename)
    print(f"preprocess_video: {video_filename} capture video")
    if not video.isOpened():
        raise RuntimeError(f"Cannot open video file: {video_filename}")
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"preprocess_video: {video_filename} w={width} h={height}")
    if width < MIN_VID_WIDTH_PX or height < MIN_VID_HEIGHT_PX:
        raise RuntimeError("Video resolution is too low")
    min_end_time = video.get(cv2.CAP_PROP_POS_MSEC) + 1000 * MIN_VID_LENGTH_SEC
    max_end_time = video.get(cv2.CAP_PROP_POS_MSEC) + 1000 * MAX_VID_LENGTH_SEC
    raw_timestamps = list()
    raw_frames = list()
    timestamp = video.get(cv2.CAP_PROP_POS_MSEC)
    max_frames = 1000000
    while max_frames>= 0 and timestamp <= max_end_time:
        max_frames -= 1
        read_ok, frame = video.read()
        if not read_ok:
            if timestamp < min_end_time:
                raise RuntimeError("Video is too short")
            else:
                break
        timestamp = video.get(cv2.CAP_PROP_POS_MSEC)
        raw_timestamps.append(timestamp)
        raw_frames.append(frame)
    video.release()
    timestamps = [int(x - raw_timestamps[0]) for x in raw_timestamps]
    fps = 1000 / np.mean(np.diff(timestamps))
    height, width, _ = raw_frames[0].shape
    stream_info = json.dumps(
        {
            "device_id": "",
            "frame_rate": round(fps, 2),
            "height": height,
            "width": width,
        }
    )
    frames_data = [
        json.dumps({"counter": i, "timestamp": t, "frame": encode_frame(frame)})
        for i, (t, frame) in enumerate(zip(timestamps, raw_frames))
    ]
    return stream_info, frames_data


async def process_video(stream_info, frames_data):
    async def consumer_handler(websocket):
        message = await websocket.recv()
        data = json.loads(message)
        return data

    async def producer_handler(websocket):
        await websocket.send(stream_info)
        for frame_info in frames_data:
            try:
                await websocket.send(frame_info)
            except websockets.ConnectionClosedOK:
                break
        else:
            await asyncio.Future()

    async def client(websocket):
        consumer_future = asyncio.create_task(consumer_handler(websocket))
        producer_future = asyncio.create_task(producer_handler(websocket))
        done_tasks, pending_tasks = await asyncio.wait(
            [consumer_future, producer_future],
            timeout=MAX_PROCESSING_TIME_SEC,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending_tasks:
            task.cancel()
        for task in done_tasks:
            if not task.exception():
                result = task.result()
                if result is not None:
                    return result
        return gen_error_result(100, "Adapter failed to get result")

    async with websockets.connect(ws_server) as websocket:
        return await client(websocket)


def worker(filename):
    print(f"worker: {filename} picked up for processing")

    video_path = input_dir.joinpath(filename)
    if video_path.stat().st_size == 0:
        print(f"worker: File {video_path} is empty.")
        return
    try:
        print("worker: preprocessing video ...")
        stream_info, frames_data = preprocess_video(str(video_path))
        print("worker: preprocessing completed")

        print("worker: sending video...")
        result = asyncio.run(process_video(stream_info, frames_data))
        print("worker: sending completed")
    except Exception as error_text:
        print(f"worker: {filename} failed: {error_text}")
        result = gen_error_result(100, error_text)

    print(f"worker: result -> {result}")
    cur_timestamp = int(datetime.now().timestamp())
    result_path = output_dir.joinpath(f"{video_path.stem}.{cur_timestamp}")
    print(f"worker: result_path ->  {result_path}")
    with open(result_path, "w") as f:
        f.write(json.dumps(result))
    try:
        video_path.unlink()
    except OSError:
        pass


def monitor_directory(queue):
    seen_files = set(p.name for p in input_dir.iterdir())
    while True:
        cur_files = set(p.name for p in input_dir.iterdir())
        for filename in cur_files - seen_files:
            queue.put(filename)
        seen_files = cur_files
        time.sleep(MONITORING_INTERVAL_SEC)


def cleanup_directory():
    while True:
        cur_timestamp = datetime.now()
        for p in chain(input_dir.iterdir(), output_dir.iterdir()):
            if not p.is_file():
                continue
            creation_timestamp = datetime.fromtimestamp(int(p.name.split(".")[1]))
            if (cur_timestamp - creation_timestamp).total_seconds() > MAX_FILE_TTL_SEC:
                try:
                    p.unlink()  # delete file
                except OSError:
                    continue
        time.sleep(CLEANUP_INTERVAL_SEC)


def main():
    task_queue = Queue()
    monitor_process = Process(target=monitor_directory, args=(task_queue,), daemon=True)
    cleanup_process = Process(target=cleanup_directory, daemon=True)
    monitor_process.start()
    cleanup_process.start()
    pool = Pool(processes=NUM_WORKERS)
    try:
        while True:
            task = task_queue.get()
            pool.apply_async(worker, args=(task,))
    except KeyboardInterrupt:
        pass
    finally:
        pool.close()
        pool.join()
        monitor_process.terminate()
        cleanup_process.terminate()


if __name__ == "__main__":
    main()
