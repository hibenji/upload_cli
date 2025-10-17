# Simple Upload Server

A minimal Python + Flask web server that allows file uploads via `curl` and provides short download links.  
Files are automatically removed after **24 hours**.

---

## Features
- Upload with `curl <url> -T file`
- Two download link styles:
  - Short ID + filename: `http://domain/abc/file.txt`
  - Long friendly ID only: `http://domain/xyz12`
- Files are stored once and cleaned up by a background scheduler after 24 hours
- Reverse proxy friendly (nginx config included)

---

## Requirements
- Python 3.11+
- Docker (optional, for containerized runs)
- Nginx (if you want to serve behind a reverse proxy)

---

## Running locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python server.py
```

By default, it listens on port **8085**.

---

## Running with Docker

### 1. Build the image
```bash
docker build -t simple-upload-server .
```

### 2. Run the container
```bash
docker run -d -p 8085:8085 --name upload simple-upload-server
```

Now the server is available at `http://localhost:8085`.

---

## Using curl

### Upload a file
```bash
curl http://your-domain.com/ -T notes.txt
```

### Example response
```
Your file has been uploaded and will be stored for 24 hours.
To download use one of the below:

wget http://your-domain.com/abc/notes.txt
========
wget http://your-domain.com/k9d3x
```

### Download options
```bash
# By short ID + filename
wget http://your-domain.com/abc/notes.txt

# By long friendly ID
wget http://your-domain.com/k9d3x
```

---

## Nginx reverse proxy

There is also an example nginx config to run the server behind a reverse proxy, just change your domain and paths as needed.

### Enable config
1. Save as `/etc/nginx/sites-available/upload.conf`
2. Symlink to `sites-enabled`:
   ```bash
   ln -s /etc/nginx/sites-available/upload.conf /etc/nginx/sites-enabled/
   ```
3. Test and reload nginx:
   ```bash
   nginx -t
   systemctl reload nginx
   ```

---

## HTTPS with Let’s Encrypt
Once your nginx reverse proxy works on port 80, enable HTTPS with:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

Certbot will automatically update your nginx config for TLS and renew certificates.

---

## Notes
- Files are cleaned up after 24 hours (configurable in code).
- Upload IDs are not persisted across server restarts — after a restart, old links will not resolve.
