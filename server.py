from flask import Flask, request, send_file, url_for
import os, secrets, string, random, time
from apscheduler.schedulers.background import BackgroundScheduler

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

# id -> filepath mapping
id_map = {}

def friendly_id(length=5):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

def cleanup_uploads(max_age=24*3600):
    now = time.time()
    deleted = 0
    for root, _, files in os.walk(UPLOAD_FOLDER):
        for f in files:
            path = os.path.join(root, f)
            try:
                if now - os.path.getmtime(path) > max_age:
                    os.remove(path)
                    deleted += 1
            except FileNotFoundError:
                pass
        if not os.listdir(root):
            try:
                os.rmdir(root)
            except OSError:
                pass
    if deleted:
        print(f"[CLEANUP] Removed {deleted} old files")

@app.route('/<path:filename>', methods=['PUT'])
def upload(filename):
    upload_id = secrets.token_urlsafe(6)
    folder = os.path.join(UPLOAD_FOLDER, upload_id)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(request.data)

    short_id = secrets.token_urlsafe(2)[:3]
    long_id  = friendly_id(5)

    id_map[short_id + ":" + filename] = filepath
    id_map[long_id] = filepath

    # get base URL (no trailing slash)
    base_url = request.host_url.rstrip("/")

    url_with_name = f"{base_url}/{short_id}/{filename}"
    url_with_id   = f"{base_url}/{long_id}"

    return (
        "Your file has been uploaded and will be stored for 24 hours.\n"
        "To download use one of the below:\n\n"
        f"wget {url_with_name}\n"
        "========\n"
        f"wget {url_with_id}\n"
    )

@app.route('/<short_id>/<path:filename>', methods=['GET'])
def download_with_name(short_id, filename):
    key = short_id + ":" + filename
    filepath = id_map.get(key)
    if not filepath or not os.path.exists(filepath):
        return "Not found.\n", 404
    return send_file(filepath, as_attachment=True)

@app.route('/<long_id>', methods=['GET'])
def download_with_id(long_id):
    filepath = id_map.get(long_id)
    if not filepath or not os.path.exists(filepath):
        return "Not found.\n", 404
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_uploads, "interval", hours=1)
    scheduler.start()

    print("[INFO] File cleanup runs every hour.")
    app.run(host="0.0.0.0", port=8085)
