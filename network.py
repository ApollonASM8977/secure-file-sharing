"""Flask server + LAN device discovery."""

import os
import socket
import logging
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, send_from_directory, jsonify

from config import FLASK_PORT, UPLOAD_FOLDER, KEYS_DIR

# Silence Flask/Werkzeug startup logs
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

flask_app = Flask(__name__)
flask_app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(KEYS_DIR, exist_ok=True)


# ── Routes ────────────────────────────────────────────────────────────────────

@flask_app.route("/")
def index():
    return jsonify({"status": "SecureShare running", "version": "2.0.0"})


@flask_app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    dest = KEYS_DIR if file.filename.endswith(".pem") else UPLOAD_FOLDER
    save_path = os.path.join(dest, os.path.basename(file.filename))
    file.save(save_path)
    return jsonify({"message": f"Received: {file.filename}"}), 200


@flask_app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    safe_name = os.path.basename(filename)
    return send_from_directory(UPLOAD_FOLDER, safe_name, as_attachment=True)


# ── Server launcher ───────────────────────────────────────────────────────────

def start_server():
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, use_reloader=False)


# ── Device Discovery ──────────────────────────────────────────────────────────

def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.168.1.1", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def _probe(ip: str):
    try:
        with socket.create_connection((ip, FLASK_PORT), timeout=0.5):
            return ip
    except OSError:
        return None


def discover_devices() -> list[str]:
    """Scan the local /24 subnet for SecureShare peers."""
    local_ip = get_local_ip()
    base = local_ip.rsplit(".", 1)[0]
    candidates = [f"{base}.{i}" for i in range(1, 255)]
    with ThreadPoolExecutor(max_workers=60) as ex:
        results = ex.map(_probe, candidates)
    return [r for r in results if r and r != local_ip]
