"""
URL Shortener - Simple Flask Web App
-------------------------------------
How it works:
  1. User submits a long URL on the homepage.
  2. We generate a random 6-character short code.
  3. We save the mapping (short code -> long URL) in a SQLite database.
  4. We show the user a short link like: http://localhost:5000/abc123
  5. When someone visits that short link, we look it up and redirect them.
"""

import random
import string
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, abort

# ── App setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)

# The SQLite database file will be created automatically in the same folder.
DATABASE = "urls.db"


# ── Database helpers ─────────────────────────────────────────────────────────

def get_db():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn


def init_db():
    """Create the urls table if it doesn't exist yet."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                short     TEXT    NOT NULL UNIQUE,   -- the 6-char code
                long_url  TEXT    NOT NULL            -- the original URL
            )
            """
        )


# ── Short-code generator ──────────────────────────────────────────────────────

def make_short_code(length=6):
    """Return a random string of letters and digits, e.g. 'aB3x9Z'."""
    characters = string.ascii_letters + string.digits   # a-z A-Z 0-9
    return "".join(random.choices(characters, k=length))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    """
    GET  → show the homepage with the input form.
    POST → shorten the submitted URL and show the result.
    """
    short_url = None   # will be filled in after a successful POST
    error     = None   # shown to the user if something goes wrong

    if request.method == "POST":
        long_url = request.form.get("long_url", "").strip()

        # Basic validation: URL must start with http:// or https://
        if not long_url.startswith(("http://", "https://")):
            error = "Please enter a valid URL starting with http:// or https://"
        else:
            # Generate a unique short code
            code = make_short_code()

            with get_db() as conn:
                # Make sure the code isn't already taken (very unlikely but safe)
                while conn.execute("SELECT 1 FROM urls WHERE short = ?", (code,)).fetchone():
                    code = make_short_code()

                conn.execute(
                    "INSERT INTO urls (short, long_url) VALUES (?, ?)",
                    (code, long_url)
                )

            # Build the full short URL to display to the user
            short_url = request.host_url + code   # e.g. http://localhost:5000/aB3x9Z

    return render_template("index.html", short_url=short_url, error=error)


@app.route("/<code>")
def redirect_to_url(code):
    """
    Look up the short code in the database and redirect to the original URL.
    If the code doesn't exist, return a 404 page.
    """
    with get_db() as conn:
        row = conn.execute("SELECT long_url FROM urls WHERE short = ?", (code,)).fetchone()

    if row is None:
        abort(404)   # short code not found

    return redirect(row["long_url"])


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()          # create the database table on first run
    app.run(debug=True)  # debug=True gives helpful error pages during development
