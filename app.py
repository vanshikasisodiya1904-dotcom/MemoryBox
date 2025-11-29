from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# In-memory database
users = {}        # {email: password}
memories = {}     # {email: [{"filename": "...", "unlock_date": "..."}]}

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class User(UserMixin):
    def __init__(self, email):
        self.id = email


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in users and users[email] == password:
            login_user(User(email))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid login")

    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in users:
            flash("Email already exists")
        else:
            users[email] = password
            memories[email] = []
            login_user(User(email))
            return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user_mem = memories.get(current_user.id, [])

    # Convert unlock_date into a datetime object
    for m in user_mem:
        try:
            m["unlock_date_obj"] = datetime.strptime(m["unlock_date"], "%Y-%m-%d")
        except:
            m["unlock_date_obj"] = datetime.now()

    # Sort by unlock date
    user_mem_sorted = sorted(user_mem, key=lambda x: x["unlock_date_obj"])

    # Separate unlocked and locked memories
    today = datetime.now()
    unlocked = [m for m in user_mem_sorted if m["unlock_date_obj"] <= today]
    locked = [m for m in user_mem_sorted if m["unlock_date_obj"] > today]

    return render_template("dashboard.html", unlocked=unlocked, locked=locked)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["file"]
        unlock_date = request.form["unlock_date"]

        if not file.filename:
            flash("Please select a file!")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        memories[current_user.id].append({
            "filename": filename,
            "unlock_date": unlock_date
        })

        flash("Memory uploaded successfully!")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
