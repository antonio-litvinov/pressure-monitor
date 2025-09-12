import os
import subprocess
from datetime import datetime
from os import getenv
from pathlib import Path
from uuid import UUID, uuid4

from flask import Flask, request, jsonify

app = Flask(__name__)

token = os.environ.get("GIGADOC_TOKEN")

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mkv", "webm", "mpg", "mpeg"}
MIN_VID_WIDTH_PX = 640
MIN_VID_HEIGHT_PX = 480
MIN_VID_LENGTH_SEC = 10


working_dir = Path(getenv("GIGADOC_ADAPTER_DIR", "/tmp/gigadoc_cache/"))
adapter_ip = getenv("GIGADOC_ADAPTER_IP", "127.0.0.1")
adapter_port = getenv("GIGADOC_ADAPTER_PORT", "5000")


input_dir = working_dir.joinpath("input")
output_dir = working_dir.joinpath("output")
input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB upload limit


def allowed_video_ext(filename):
    return "." in filename and filename.rsplit(".")[-1].lower() in ALLOWED_VIDEO_EXTENSIONS


def get_video_metadata(filename):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                filename,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        width, height, duration = result.stdout.strip().split("\n")
        try:  # duration may be "0.0" or "N/A"
            duration = float(duration)
            duration = None if duration == 0 else duration
        except ValueError:
            duration = None
        return int(width), int(height), duration
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


@app.route("/upload", methods=["POST"])
def upload_file():

    # Проверка Bearer токена
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Отсутствует или неверный Bearer токен'}), 401
    
    bearer_token = auth_header.split(' ')[1]
    if bearer_token != str(token):
        return jsonify({'error': 'Неверный токен авторизации'}), 401

    if "file" not in request.files:
        return "File is not attached", 400

    file = request.files["file"]
    
    if file.filename == "":
        return "Empty filename", 400

    if not allowed_video_ext(file.filename):
        return "Unsupported file extension", 400
    
    cur_uuid = uuid4()
    cur_timestamp = int(datetime.now().timestamp())
    save_path = input_dir.joinpath(f"{cur_uuid.hex}.{cur_timestamp}")
    
    try:
        file.save(save_path)
    except Exception:
        return "Failed to cache file", 500
    
    result = get_video_metadata(save_path)
    
    if result is not None:
        width, height, duration = result
        if width < MIN_VID_WIDTH_PX or height < MIN_VID_HEIGHT_PX:
            return "Video frame size too small", 400
        if duration is not None and duration < MIN_VID_LENGTH_SEC:
            return "Video too short", 400
    
    return cur_uuid.hex, 200


@app.route("/result/<uuid_hex>", methods=["GET"])
def download_file(uuid_hex):
    try:
        video_uuid = UUID(uuid_hex)
    except ValueError:
        return "Invalid ID", 400
    try:
        result_path = next(p for p in output_dir.iterdir() if p.stem == video_uuid.hex)
        with open(result_path, "r") as file:
            json_content = file.read()
        return json_content, 200, {"Content-Type": "application/json"}
    except OSError:
        return "Failed to read result", 503
    except StopIteration:
        pass
    if any(p.stem == video_uuid.hex for p in input_dir.iterdir()):
        return "Processing in progress", 204
    else:
        return "ID not found", 404


if __name__ == "__main__":
    app.run(host=adapter_ip, port=int(adapter_port), debug=True)
    # normally run using: gunicorn -w 4 -b 127.0.0.1:500 adapter_interface:app
    # for testing use: curl -X POST -F "file=@video.mkv" http://127.0.0.1:5000/upload
