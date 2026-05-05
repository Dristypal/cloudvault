# ☁️ CloudVault

A secure, encrypted cloud file storage web application built with **Flask**, **AWS S3**, and **OpenAI**. CloudVault lets users upload, download, and manage files with end-to-end encryption, an admin dashboard, and an integrated AI assistant.

---

## ✨ Features

- 🔐 **Encrypted File Storage** — Files are encrypted using Fernet symmetric encryption before being uploaded to AWS S3
- 👤 **User Authentication** — Register and login with hashed passwords via Flask-Login and Werkzeug
- ☁️ **AWS S3 Backend** — Each user gets their own isolated storage prefix in S3
- 📊 **Admin Dashboard** — View total users, files, and storage usage with bar and doughnut charts
- 📈 **Activity Logging** — All uploads and deletions are recorded in a SQLite activity log
- 🤖 **AI Chat Assistant** — Integrated GPT-4o-mini assistant to help users with storage, encryption, and AWS questions
- 📁 **File Sharing** — Public token-based file sharing support
- 📱 **Responsive UI** — Mobile-friendly layout with a collapsible sidebar

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Auth | Flask-Login, Werkzeug |
| Storage | AWS S3 (boto3) |
| Encryption | cryptography (Fernet) |
| Database | SQLite |
| AI Assistant | OpenAI GPT-4o-mini |
| Frontend | HTML, CSS, Chart.js |

---

## 📁 Project Structure

```
cloudvault/
├── app.py                  # Main Flask application
├── secret.key              # Auto-generated Fernet encryption key (gitignored)
├── database.db             # SQLite database (gitignored)
├── static/
│   └── style.css           # Global stylesheet
└── templates/
    ├── index.html          # Main dashboard / file manager
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── admin.html          # Admin panel with charts
    └── analytics.html      # Analytics view
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- An AWS account with an S3 bucket
- An OpenAI API key

### 1. Clone the Repository

```bash
git clone https://github.com/Dristypal/cloudvault.git
cd cloudvault
```

### 2. Install Dependencies

```bash
pip install flask flask-login werkzeug boto3 cryptography python-dotenv openai
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Set Up Your S3 Bucket

- Create an S3 bucket named `cloudvault-storage-system` in the `ap-south-1` (Mumbai) region, or update the `S3_BUCKET` and `region_name` values in `app.py` to match your own bucket.

### 5. Run the App

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`.

---

## 🔒 Security Notes

- The `secret.key` file is auto-generated on first run and is used to encrypt/decrypt all files. **Do not delete or lose this file** — without it, existing encrypted files cannot be recovered.
- Passwords are stored as bcrypt-style hashes using Werkzeug.
- Each user's files are stored under their unique user ID prefix in S3, providing logical isolation.
- The `secret.key` and `database.db` files should be added to `.gitignore` and never committed to version control.

---

## 📦 Storage Limits

Each user has a default storage limit of **5 GB** (5120 MB), enforced at the application level.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 👩‍💻 Author

**Dristypal** — [GitHub](https://github.com/Dristypal)
