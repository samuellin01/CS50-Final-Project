import os
import io
import calendar
import datetime
import matplotlib.pyplot
import astropy.time
import astropy.units as units
import sqlite3
 
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, Response, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from time import strptime
from iso3166 import countries
from astropy.coordinates import EarthLocation
from math import modf
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from helpers import apology, login_required, locator, draw_template, draw_constellations, draw_vision, draw_moon



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///skymap.db")
skymap_db = sqlite3.connect("skymap.db", check_same_thread=False)
cur1 = skymap_db.cursor()

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        # return redirect("/")
        return redirect("/timeplace")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    # return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensures both passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Query database for username
        user = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Checks to see if the username exists
        if len(user) == 1:
            return apology("username already exists", 400)

        # Generates a hashed password
        hash_password = generate_password_hash(request.form.get("password"))

        # Inserts new user into users
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), hash_password)

        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/timeplace", methods=["GET", "POST"])
def timeplace():
    months = []
    nations = []
    message = ""
    # Generate list of months
    for i in range(1, 13):
        months.append(datetime.date(2020, i, 1).strftime('%B'))
    # Generate list of countries from iso1366 API
    for c in countries:
        nations.append(c.name)
    # GET: Loads form requesting a place and time, the latter is defaulted to current local time
    if request.method == "GET":
        return render_template("timeplace.html", message=message, months=months, nations=nations, present_month=datetime.datetime.now().strftime('%B'), present_day=int(datetime.datetime.now().strftime('%d')), present_year=datetime.datetime.now().strftime('%Y'), present_hour=datetime.datetime.now().strftime('%H'), present_minute=datetime.datetime.now().strftime('%M'))
    # POST: Retrives timeplace form's data, validates and stores the data, and redirects to skymap
    else:
        zipcode = request.form.get("zipcode")
        nation = request.form.get("country")
        month = strptime(request.form.get("month")[0:3], '%b').tm_mon
        day = int(request.form.get("day"))
        year = int(request.form.get("year"))
        hour = int(request.form.get("hour"))
        minute = int(request.form.get("minute"))
        try:
            date = datetime.date(year=year, month=month, day=day)
        except ValueError:
            message = "Invalid Date"
        if locator(zipcode, nation) == None:
            message = "Invalid/Missing Location"
        elif year < 2000:
            message = "Date must be after January 1, 2000"
        elif year > 2040:
            message = "Date must be before December 31st, 2039"
        if message == "":
            # Store both the time to be used on sky map and time request is made
            requesttime = datetime.datetime(year, month, day, hour, minute)
            timestamp = datetime.datetime.now()
            cur1.execute("INSERT INTO timeplaces (username, zipcode, country, requesttime, timestamp) VALUES (?, ?, ?, ?, ?)", ("Null", zipcode, nation, requesttime, timestamp))
            skymap_db.commit()
            return redirect(url_for('skymap'))
        else:
            return render_template("timeplace.html", message=message, months=months, nations=nations, present_month=datetime.datetime.now().strftime('%B'), present_day=int(datetime.datetime.now().strftime('%d')), present_year=datetime.datetime.now().strftime('%Y'), present_hour=datetime.datetime.now().strftime('%H'), present_minute=datetime.datetime.now().strftime('%M'))

# Called only from /skymap route to generate skymap image using matplotlib
@app.route("/skymap.png")
def skymap_png():
    # Find latest timeplace request from user
    for item in cur1.execute("SELECT * FROM timeplaces ORDER BY timestamp DESC LIMIT 1"):
        # Convert time to Coordinated Universal Time
        utc_difference = datetime.datetime.now()-datetime.datetime.utcnow()
        date_time_obj = datetime.datetime.strptime(item[3], '%Y-%m-%d %H:%M:%S')
        input_time = astropy.time.Time(date_time_obj - utc_difference)
        input_loc = EarthLocation(lat=float(locator(item[1], item[2])["lat"])*units.deg, lon=float(locator(item[1], item[2])["lon"])*units.deg)
        # Plot skymap and return a PNG
        matplotlib.pyplot.style.use('dark_background')
        fig, ax = draw_template()
        draw_constellations(ax)
        draw_vision(ax, input_time, input_loc)
        draw_moon(ax, input_time, input_loc)
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return Response(output.getvalue(), mimetype="image/png")

@app.route("/skymap")
def skymap():
    # Renders skymap labeled with location and time
    for item in cur1.execute("SELECT * FROM timeplaces ORDER BY timestamp DESC LIMIT 1"):
        lat = round(float(locator(item[1], item[2])["lat"]), 3)
        lon = round(float(locator(item[1], item[2])["lon"]), 3)
        zipcode = item[1]
        country = item[2]
        time = item[3][0:-3]
        return render_template("skymap.html", lat=lat, lon=lon, zipcode=zipcode, country=country, time=time)
