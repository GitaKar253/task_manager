import os

from cs50 import SQL
from flask import Flask, session, redirect, render_template
from flask_session import Session
from tempfile import mkdtemp
from helpers import usd


from users import users_bp
from tasks import tasks_bp

# Configure application
app = Flask(__name__)

app.register_blueprint(users_bp)
app.register_blueprint(tasks_bp)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///task_manager.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
def welcome_page():
    # If user is logged in, redirect to tasks page
    if session.get("user_id"):
        return redirect("/tasks")

    # Otherwise show welcome page
    return render_template("welcome_page.html")

