import sqlite3
from os import path
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for

template_folder = path.abspath('./pages')

app = Flask(__name__, template_folder=template_folder)

DATABASE = Path(__file__).with_name("baking_contest.db")

def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  
    return conn


def init_db():
    """Create tables if they do not already exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS BakingContestPeople (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT NOT NULL,
            security_level INTEGER NOT NULL,
            login_password TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS BakingContestEntry (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            num_excellent INTEGER NOT NULL,
            num_ok INTEGER NOT NULL,
            num_bad INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES BakingContestPeople(id)
        );
    """)

    conn.commit()
    conn.close()


init_db()



@app.route("/")
def home():

    return render_template("home.html")


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "GET":
        # Show the form
        return render_template("newbaking.html")

    # POST: process form submission
    name = request.form.get("name", "").strip()
    age_str = request.form.get("age", "").strip()
    phone = request.form.get("phone", "").strip()
    sec_level_str = request.form.get("security_level", "").strip()
    password = request.form.get("password", "").strip()

    errors = []

    # ---- Input validation (matches assignment spec) ----

    # Name: not empty or spaces only
    if not name:
        errors.append("Name cannot be empty or spaces only.")

    # Age: whole number 1–120
    try:
        age = int(age_str)
        if age <= 0 or age >= 121:
            errors.append("Age must be a whole number between 1 and 120.")
    except ValueError:
        errors.append("Age must be a whole number between 1 and 120.")

    # Phone number: not empty or spaces only
    if not phone:
        errors.append("Phone Number cannot be empty or spaces only.")

    # Security level: numeric between 1 and 3
    try:
        sec_level = int(sec_level_str)
        if sec_level < 1 or sec_level > 3:
            errors.append("Security Level must be a number between 1 and 3.")
    except ValueError:
        errors.append("Security Level must be a number between 1 and 3.")

    # Password: not empty or spaces only
    if not password:
        errors.append("Login Password cannot be empty or spaces only.")

    # ---- If any errors, send them to Result page ----
    if errors:
        msg = "Record NOT added:<br>" + "<br>".join(errors)
        # redirect to /result with msg in query string
        return redirect(url_for("result", msg=msg))

    # ---- If valid, insert into BakingContestPeople ----
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO BakingContestPeople (name, age, phone, security_level, login_password)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, age, phone, sec_level, password),
    )
    conn.commit()
    conn.close()

    msg = f"Record added successfully for user: {name}"
    return redirect(url_for("result", msg=msg))


@app.route("/list_users")
def list_users():
    """List Baking Contest Users page."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT name, age, phone, security_level, login_password
        FROM BakingContestPeople
        ORDER BY name;
        """
    ).fetchall()
    conn.close()

    # Pass users to template
    return render_template("listbaking.html", users=rows)


@app.route("/list_results")
def list_results():
    """List Contest Results page."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT entry_id, user_id, item_name,
               num_excellent, num_ok, num_bad
        FROM BakingContestEntry
        ORDER BY entry_id;
        """
    ).fetchall()
    conn.close()

    return render_template("bakingresults.html", entries=rows)


@app.route("/result")
def result():
    """Result page: shows success or error message + link back home."""
    msg = request.args.get("msg", "")

    return render_template("result.html", msg=msg)


@app.route("/api/test_insert_user")
def api_test_insert_user():
    """Insert a test user into BakingContestPeople and report what happened."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO BakingContestPeople (name, age, phone, security_level, login_password)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Test User", 25, "555-1234", 2, "secret123"),
    )
    conn.commit()

    new_id = cur.lastrowid
    conn.close()

    return f"Inserted test user with id = {new_id}\n"


@app.route("/api/test_list_users")
def api_test_list_users():
    """Return all users as JSON so you can confirm the database is working."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, name, age, phone, security_level, login_password
        FROM BakingContestPeople
        ORDER BY id;
        """
    ).fetchall()
    conn.close()

    users = [dict(row) for row in rows]

    return {"users": users}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
