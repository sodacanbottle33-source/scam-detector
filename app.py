import os
import uuid
import ipaddress
import socket
from urllib.parse import urlparse

import requests
import yt_dlp
from flask import Flask, request, render_template, redirect, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect

from models import db, User, Scan
from advanced_ai_engine import analyze_message
from ai_voice_detector import detect_ai_voice
from ai_video_detector import detect_ai_video

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-insecure-key-CHANGE-ME")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

db.init_app(app)
csrf = CSRFProtect(app)

UPLOAD_DIR = "uploads_tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "avi", "mkv"}
MAX_REMOTE_VIDEO_BYTES = 100 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    return redirect("/dashboard" if current_user.is_authenticated else "/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif User.query.filter_by(username=username).first():
            error = "Username already exists."
        else:
            user = User(username=username, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            return redirect("/login")

    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/dashboard")

        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


def save_upload_safely(file_storage):
    original_name = file_storage.filename or "upload.bin"
    extension = original_name.rsplit(".", 1)[1].lower() if "." in original_name else "bin"
    filename = f"{uuid.uuid4().hex}.{extension}"
    path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(path)
    return path


def is_public_http_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False

        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
        return True
    except Exception:
        return False


def is_youtube_url(url):
    try:
        hostname = (urlparse(url).hostname or "").lower()
        return (
            hostname == "youtu.be"
            or hostname.endswith(".youtu.be")
            or hostname == "youtube.com"
            or hostname.endswith(".youtube.com")
        )
    except Exception:
        return False


def guess_video_extension(url, content_type):
    parsed = urlparse(url)
    path = parsed.path.lower()

    if "." in path:
        extension = path.rsplit(".", 1)[1]
        if extension in ALLOWED_VIDEO_EXTENSIONS:
            return extension

    mapping = {
        "video/mp4": "mp4",
        "video/webm": "webm",
        "video/quicktime": "mov",
        "video/x-msvideo": "avi",
        "video/x-matroska": "mkv",
    }
    clean_type = (content_type or "").split(";")[0].strip().lower()
    return mapping.get(clean_type)


def download_direct_video(url):
    if not is_public_http_url(url):
        raise ValueError("Only public HTTP or HTTPS video URLs are allowed.")

    with requests.get(
        url,
        stream=True,
        timeout=(10, 60),
        allow_redirects=True,
        headers={"User-Agent": "AI-Scam-Detector/1.0"},
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        extension = guess_video_extension(response.url, content_type)

        if extension is None:
            raise ValueError(
                "This is not a direct video-file URL. Use a direct .mp4, .webm, .mov, .avi, or .mkv link, or paste a YouTube URL."
            )

        declared_length = response.headers.get("Content-Length")
        if declared_length and int(declared_length) > MAX_REMOTE_VIDEO_BYTES:
            raise ValueError("Remote video is larger than 100 MB.")

        filename = f"{uuid.uuid4().hex}.{extension}"
        path = os.path.join(UPLOAD_DIR, filename)
        downloaded = 0

        try:
            with open(path, "wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_REMOTE_VIDEO_BYTES:
                        raise ValueError("Remote video is larger than 100 MB.")
                    output.write(chunk)
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            raise

    return path


def download_youtube_video(url):
    if not is_youtube_url(url):
        raise ValueError("This is not a valid YouTube URL.")

    unique_id = uuid.uuid4().hex
    output_template = os.path.join(UPLOAD_DIR, f"{unique_id}.%(ext)s")

    options = {
        "format": "best[ext=mp4][filesize<100M]/best[filesize<100M]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "merge_output_format": "mp4",
        "max_filesize": MAX_REMOTE_VIDEO_BYTES,
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)

            for item in info.get("requested_downloads") or []:
                filepath = item.get("filepath")
                if filepath and os.path.exists(filepath):
                    return filepath

            prepared_path = downloader.prepare_filename(info)
            if prepared_path and os.path.exists(prepared_path):
                return prepared_path

    except yt_dlp.utils.DownloadError as error:
        raise ValueError(f"YouTube download failed: {error}") from error

    matches = [
        os.path.join(UPLOAD_DIR, name)
        for name in os.listdir(UPLOAD_DIR)
        if name.startswith(unique_id + ".")
    ]

    if matches:
        return max(matches, key=os.path.getmtime)

    raise FileNotFoundError("YouTube download finished, but the video file was not found.")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result = None

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            try:
                result = analyze_message(message)
            except Exception as error:
                result = {"score": 0, "level": "ERROR", "reasons": [str(error)]}

            scan = Scan(
                message=message,
                score=result.get("score", 0),
                level=result.get("level", "ERROR"),
                user_id=current_user.id,
            )
            db.session.add(scan)
            db.session.commit()

    scans = (
        Scan.query
        .filter_by(user_id=current_user.id)
        .order_by(Scan.id.desc())
        .all()
    )

    return render_template("dashboard.html", result=result, scans=scans)


@app.route("/analyze_voice", methods=["POST"])
@csrf.exempt
@login_required
def analyze_voice():
    audio = request.files.get("audio")
    if not audio:
        return jsonify({"error": "No audio file received."}), 400

    path = save_upload_safely(audio)
    try:
        result = detect_ai_voice(path)
        result["saved_file"] = path
        result["file_size"] = os.path.getsize(path)
        return jsonify(result)
    except Exception as error:
        return jsonify({"error": str(error), "saved_file": path}), 500


@app.route("/analyze_video", methods=["POST"])
@csrf.exempt
@login_required
def analyze_video():
    video = request.files.get("video")
    if not video or video.filename == "":
        return jsonify({"error": "No video file received."}), 400

    extension = video.filename.rsplit(".", 1)[1].lower() if "." in video.filename else ""
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return jsonify({"error": "Unsupported video format."}), 400

    path = save_upload_safely(video)
    try:
        result = detect_ai_video(path)
        result["saved_file"] = path
        result["file_size"] = os.path.getsize(path)
        return jsonify(result)
    except Exception as error:
        return jsonify({"error": str(error), "saved_file": path}), 500


@app.route("/analyze_video_url", methods=["POST"])
@csrf.exempt
@login_required
def analyze_video_url():
    payload = request.get_json(silent=True) or {}
    video_url = str(payload.get("url", "")).strip()

    if not video_url:
        return jsonify({"error": "No video URL provided."}), 400

    try:
        if is_youtube_url(video_url):
            path = download_youtube_video(video_url)
            source_type = "youtube"
        else:
            path = download_direct_video(video_url)
            source_type = "direct"

        result = detect_ai_video(path)
        result["saved_file"] = path
        result["file_size"] = os.path.getsize(path)
        result["source_url"] = video_url
        result["source_type"] = source_type
        return jsonify(result)

    except requests.RequestException as error:
        return jsonify({"error": f"Could not download the video: {error}"}), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug_mode)