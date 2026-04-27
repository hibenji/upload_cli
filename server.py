from flask import Flask, jsonify, render_template, request, send_file
import os, secrets, string, random, time
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

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

def get_base_url():
    return request.url_root.rstrip("/")

def get_request_protocol():
    return "https" if request.is_secure else "http"

def normalize_upload_name(filename):
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    filename = secure_filename(filename)
    if not filename:
        return None
    return filename

def save_upload(filename, stream):
    filename = normalize_upload_name(filename)
    if not filename:
        return None

    upload_id = secrets.token_urlsafe(6)
    folder = os.path.join(UPLOAD_FOLDER, upload_id)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    short_id = secrets.token_urlsafe(2)[:3]
    long_id  = friendly_id(5)

    id_map[short_id + ":" + filename] = filepath
    id_map[long_id] = filepath

    base_url = get_base_url()
    url_with_name = f"{base_url}/{short_id}/{filename}"
    url_with_id   = f"{base_url}/{long_id}"

    return {
        "filename": filename,
        "url_with_name": url_with_name,
        "url_with_id": url_with_id,
        "wget_with_name": f"wget {url_with_name}",
        "wget_with_id": f"wget {url_with_id}",
    }

def text_upload_response(upload_links):
    return (
        "Your file has been uploaded and will be stored for 24 hours.\n"
        "To download use one of the below:\n\n"
        f"{upload_links['wget_with_name']}\n"
        "========\n"
        f"{upload_links['wget_with_id']}\n"
    )

def wants_json_response():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )

@app.route('/', methods=['GET'])
def index():
    return render_template(
        "index.html",
        base_url=get_base_url(),
        protocol=get_request_protocol(),
        result=None,
        error=None,
    )

@app.route('/upload', methods=['POST'])
def upload_from_browser():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        if wants_json_response():
            return jsonify({"error": "Choose a file before uploading."}), 400
        return render_template(
            "index.html",
            base_url=get_base_url(),
            protocol=get_request_protocol(),
            result=None,
            error="Choose a file before uploading.",
        ), 400

    upload_links = save_upload(uploaded_file.filename, uploaded_file.stream)
    if not upload_links:
        if wants_json_response():
            return jsonify({"error": "That filename could not be used."}), 400
        return render_template(
            "index.html",
            base_url=get_base_url(),
            protocol=get_request_protocol(),
            result=None,
            error="That filename could not be used.",
        ), 400

    if wants_json_response():
        return jsonify(upload_links)

    return render_template(
        "index.html",
        base_url=get_base_url(),
        protocol=get_request_protocol(),
        result=upload_links,
        error=None,
    )

@app.route('/<filename>', methods=['PUT'])
def upload(filename):
    upload_links = save_upload(filename, request.stream)
    if not upload_links:
        return "Invalid filename.\n", 400
    return text_upload_response(upload_links)

@app.route('/<path:filename>', methods=['PUT'])
def reject_nested_upload(filename):
    return "Nested upload paths are not supported.\n", 400

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
    port = int(os.environ.get("PORT", "8086"))
    app.run(host="0.0.0.0", port=port)
