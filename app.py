import os
import sqlite3
import io
import boto3
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from botocore.exceptions import ClientError
from openai import OpenAI

# ================= LOAD ENV =================
load_dotenv()

# ================= FLASK APP =================
app = Flask(__name__)
app.secret_key = "dristy-cloud-backup-secret-2026"

# ================= AWS S3 CONFIG =================
S3_BUCKET = "cloudvault-storage-system"

s3 = boto3.client(
    "s3",
    region_name="ap-south-1"
)

# ================= OPENAI CONFIG =================
client = OpenAI()

# ================= ENCRYPTION SETUP =================
if not os.path.exists("secret.key"):
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)

with open("secret.key", "rb") as f:
    key = f.read()

cipher = Fernet(key)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Activity log table
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # File sharing table
    c.execute("""
        CREATE TABLE IF NOT EXISTS shared_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            public_token TEXT
        )
    """)

    conn.commit()
    conn.close()

# ================= LOGIN SETUP =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = str(id)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ================= HOME =================
@app.route("/")
@login_required
def home():
    USER_STORAGE_LIMIT_MB = 5120  # 5GB per user

    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"{current_user.id}/"
        )
    except ClientError as e:
        print("S3 Error:", e)
        return "Storage connection error"

    files = []
    total_size_bytes = 0

    if "Contents" in response:
        for obj in response["Contents"]:
            filename = obj["Key"].split("/")[-1]
            if filename:
                files.append(filename)
                total_size_bytes += obj["Size"]

    total_size = round(total_size_bytes / (1024 * 1024), 2)

    return render_template(
        "index.html",
        files=files,
        total_size=total_size,
        max_storage=USER_STORAGE_LIMIT_MB
    )

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            conn.close()
            return "Username already exists"
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            login_user(User(user[0]))
            return redirect(url_for("home"))

        return "Invalid Credentials"

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ================= UPLOAD =================
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")

    if not file:
        return redirect(url_for("home"))

    encrypted_data = cipher.encrypt(file.read())

    try:
        s3.upload_fileobj(
            io.BytesIO(encrypted_data),
            S3_BUCKET,
            f"{current_user.id}/{file.filename}"
        )

        # ✅ ADD THIS PART (Activity Logging)
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO activity (user_id, action) VALUES (?, ?)",
            (current_user.id, f"Uploaded {file.filename}")
        )
        conn.commit()
        conn.close()

    except ClientError as e:
        print("Upload Error:", e)
        return "Upload failed"

    return redirect(url_for("home"))

# ================= DOWNLOAD =================
@app.route("/download/<filename>")
@login_required
def download(filename):
    file_key = f"{current_user.id}/{filename}"

    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        encrypted_data = response["Body"].read()
        decrypted_data = cipher.decrypt(encrypted_data)

        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=filename
        )

    except ClientError as e:
        print("Download Error:", e)
        return "Download failed"

# ================= DELETE =================
@app.route("/delete/<filename>")
@login_required
def delete(filename):
    file_key = f"{current_user.id}/{filename}"

    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=file_key)

        # ✅ ADD ACTIVITY LOGGING HERE
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO activity (user_id, action) VALUES (?, ?)",
            (current_user.id, f"Deleted {filename}")
        )
        conn.commit()
        conn.close()

    except ClientError as e:
        print("Delete Error:", e)
        return "Delete failed"

    return redirect(url_for("home"))

# ================= AI CHAT =================
@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"reply": "Invalid request."})

    user_message = data["message"]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are CloudVault AI assistant. Help users with AWS S3, encryption, file storage, and security."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        reply = response.choices[0].message.content.strip()

        return jsonify({"reply": reply})

    except Exception as e:
        print("AI Error:", str(e))
        return jsonify({"reply": "AI is temporarily unavailable."})
# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)