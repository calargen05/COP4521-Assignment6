import sqlite3
from os import path
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from crypto_utils import encrypt_str, decrypt_str
from functools import wraps

template_folder = path.abspath('./pages')
app = Flask(__name__, template_folder=str(template_folder))

# SECURITY: secret key for session; set a strong random secret on linprog
app.secret_key = (Path(__file__).with_name("flask_secret.key").read_bytes()
                  if Path(__file__).with_name("flask_secret.key").exists()
                  else None)  # you should create this file with proper key

DATABASE = Path(__file__).with_name("baking_contest.db")

def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  
    return conn

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapped

def role_required(min_level):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            if session.get("security_level", 0) < min_level:
                # logged in but insufficient privilege: page not found per spec
                return render_template("access_denied.html"), 404
            return f(*args, **kwargs)
        return wrapped
    return decorator

# def init_db():
#     """Create tables if they do not already exist."""
#     conn = get_db_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS BakingContestPeople (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             age INTEGER NOT NULL,
#             phone TEXT NOT NULL,
#             security_level INTEGER NOT NULL,
#             login_password TEXT NOT NULL
#         );
#     """)

#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS BakingContestEntry (
#             entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             item_name TEXT NOT NULL,
#             num_excellent INTEGER NOT NULL,
#             num_ok INTEGER NOT NULL,
#             num_bad INTEGER NOT NULL,
#             FOREIGN KEY (user_id) REFERENCES BakingContestPeople(id)
#         );
#     """)

#     conn.commit()
#     conn.close()


# init_db()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    # The Name field is encrypted in DB. We should encrypt the provided username
    enc_username = encrypt_str(username)
    # Query by encrypted name
    cur.execute("SELECT id, name, age, phone, security_level, login_password FROM BakingContestPeople WHERE name = ?", (enc_username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        # user not found
        return render_template("login.html", error="invalid username and/or password!")

    # decrypt password from DB and compare
    stored_pw_enc = row["login_password"]
    stored_pw = decrypt_str(stored_pw_enc)

    if stored_pw != password:
        return render_template("login.html", error="invalid username and/or password!")

    # Login success: set session
    session["user_id"] = row["id"]
    session["username"] = decrypt_str(row["name"])
    session["security_level"] = row["security_level"]
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/my_entries")
@login_required
def my_entries():
    user_id = session["user_id"]
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT item_name, num_excellent, num_ok, num_bad
        FROM BakingContestEntry
        WHERE user_id = ?
        ORDER BY entry_id
    """, (user_id,)).fetchall()
    conn.close()
    return render_template("my_entries.html", entries=rows)


@app.route("/")
def home():

    return render_template("home.html")


# --- Add a contest entry (level >=1) ---
@app.route("/add_entry", methods=["GET", "POST"])
@login_required
def add_entry():
    if request.method == "GET":
        return render_template("add_entry.html")

    name = request.form.get("item_name", "").strip()
    excellent = request.form.get("num_excellent", "").strip()
    ok = request.form.get("num_ok", "").strip()
    bad = request.form.get("num_bad", "").strip()

    errors = []
    if not name:
        errors.append("Name of Baking Item cannot be empty or spaces only.")

    def parse_nonneg_int(s, field):
        try:
            v = int(s)
            if v < 0:
                raise ValueError()
            return v
        except:
            errors.append(f"{field} must be an integer >= 0")
            return None

    ex = parse_nonneg_int(excellent, "Num Excellent Votes")
    okv = parse_nonneg_int(ok, "Num Ok Votes")
    badv = parse_nonneg_int(bad, "Num Bad Votes")

    if errors:
        msg = "Record NOT added:<br>" + "<br>".join(errors)
        return redirect(url_for("result", msg=msg))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO BakingContestEntry (user_id, item_name, num_excellent, num_ok, num_bad)
        VALUES (?, ?, ?, ?, ?)
    """, (session["user_id"], name, ex, okv, badv))
    conn.commit()
    conn.close()

    msg = f"Record added successfully for entry: {name}"
    return redirect(url_for("result", msg=msg))

# --- Add a new user (only level 3) ---
@app.route("/add_user", methods=["GET", "POST"])
@role_required(3)
def add_user_admin():
    if request.method == "GET":
        return render_template("newbaking.html")
    # fields: name, age, phone, security_level, password
    name = request.form.get("name", "").strip()
    age_str = request.form.get("age", "").strip()
    phone = request.form.get("phone", "").strip()
    sec_level_str = request.form.get("security_level", "").strip()
    password = request.form.get("password", "").strip()

    errors = []
    if not name:
        errors.append("Name cannot be empty or spaces only.")
    try:
        age = int(age_str)
        if age <= 0 or age >= 121:
            errors.append("Age must be a whole number between 1 and 120.")
    except:
        errors.append("Age must be a whole number between 1 and 120.")
    if not phone:
        errors.append("Phone Number cannot be empty or spaces only.")
    try:
        sec_level = int(sec_level_str)
        if sec_level < 1 or sec_level > 3:
            errors.append("Security Level must be a number between 1 and 3.")
    except:
        errors.append("Security Level must be a number between 1 and 3.")
    if not password:
        errors.append("Login Password cannot be empty or spaces only.")

    if errors:
        msg = "Record NOT added:<br>" + "<br>".join(errors)
        return redirect(url_for("result", msg=msg))

    # encrypt sensitive fields
    enc_name = encrypt_str(name)
    enc_phone = encrypt_str(phone)
    enc_pw = encrypt_str(password)

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO BakingContestPeople (name, age, phone, security_level, login_password)
        VALUES (?, ?, ?, ?, ?)
    """, (enc_name, age, enc_phone, sec_level, enc_pw))
    conn.commit()
    conn.close()

    msg = f"Record added successfully for user: {name}"
    return redirect(url_for("result", msg=msg))

# --- List users (role >=2) - decrypt before display ---
@app.route("/list_users")
@role_required(2)
def list_users():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, name, age, phone, security_level, login_password
        FROM BakingContestPeople
        ORDER BY name;
    """).fetchall()
    conn.close()

    # decrypt sensitive fields, store as list of dicts
    users = []
    for r in rows:
        users.append({
            "id": r["id"],
            "name": decrypt_str(r["name"]),
            "age": r["age"],
            "phone": decrypt_str(r["phone"]),
            "security_level": r["security_level"],
            "login_password": decrypt_str(r["login_password"]),
        })

    return render_template("listbaking.html", users=users)

# --- result route (show msg) ---
@app.route("/result")
@login_required
def result():
    msg = request.args.get("msg", "")
    return render_template("result.html", msg=msg)

# --- catch-all for unauthorized pages, optional ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    # For linprog use 0.0.0.0 and a port allowed by school. But in production use gunicorn.
    app.run(host="0.0.0.0", port=8080, debug=True)