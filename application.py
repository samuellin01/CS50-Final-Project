import matplotlib
# Specify 'Agg' as backend at the very beginning of the program before imports
matplotlib.use('Agg')

import matplotlib.pyplot
import os
import io
import calendar
import datetime
import astropy.time
import astropy.units as units
import sqlite3
import requests, json
import numpy
import logging

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
from astropy.coordinates import SkyCoord, get_moon

from helpers import login_required, locator


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

# Turn off matplotlib debug log messages
logging.basicConfig()
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

# Configure sqlite3 to use SQL
userdata_db = sqlite3.connect("userdata.db", check_same_thread=False)
cur1 = userdata_db.cursor()

# Initialize stars and constellations SQL databases
stars_db = sqlite3.connect("stars.db", check_same_thread=False)
constellations_db = sqlite3.connect("constellations.db", check_same_thread=False)
s = stars_db.cursor()
c = constellations_db.cursor()

@app.route("/")
@login_required
def index():
    cur1.execute("SELECT * FROM timeplaces WHERE username = ? ORDER BY timestamp", (session["username"],))
    search_history = cur1.fetchall()
    return render_template("index.html", search_history=search_history)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    message = ""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            message = "Missing username"
            return render_template("login.html", message=message)
        
        # Ensure password was submitted
        elif not request.form.get("password"):
            message = "Missing password"
            return render_template("login.html", message=message)

        # Query database for username
        cur1.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        matches = cur1.fetchall()
        # Ensure username exists and password is correct
        if len(matches) != 1 or not check_password_hash(matches[0][2], request.form.get("password")):
            message = "Invalid username and/or password"
            return render_template("login.html", message=message)
        
        # Remember which user has logged in
        session["user_id"] = matches[0][0]
        session["username"] = matches[0][1]
        # Redirect user to home page
        # return redirect("/")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    # return redirect("/")
    return render_template("login.html", message="")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()
    message = ""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            message = "Must provide username"
            return render_template("register.html", message=message)

        # Ensure password was submitted
        elif not request.form.get("password"):
            message = "Must provide password"
            return render_template("register.html", message=message)

        # Ensures both passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            message = "Passwords don't match"
            return render_template("register.html", message=message)

        # Query database for username
        cur1.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))

        # Checks to see if the username exists
        if len(cur1.fetchall()) == 1:
            message = "Username already exists"
            return render_template("register.html", message=message)

        # Generates a hashed password
        hash_password = generate_password_hash(request.form.get("password"))
        cur1.execute("SELECT * FROM users")
        total_users = len(cur1.fetchall())
        # Inserts new user into users
        cur1.execute("INSERT INTO users (id, username, hash) VALUES(?, ?, ?)", (total_users+1, request.form.get("username"), hash_password))
        userdata_db.commit()
        session["user_id"] = total_users + 1
        session["username"] = request.form.get("username")
        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", message="")

# Uses OpenWeatherMap to provide current weather for locations in search history
# Learned to write this function from documentation in https://openweathermap.org/current
@app.route("/weather")
@login_required
def weather():
    API_endpoint = "http://api.openweathermap.org/data/2.5/weather?"
    join_1 = "&appid="
    API_key = "f85761c7a2fc0e62714200e820d3f3d6"
    cur1.execute("SELECT DISTINCT zipcode, country FROM timeplaces WHERE username = ? ORDER BY timestamp", (session["username"],))
    search_history = cur1.fetchall()
    weather = []
    current_time = datetime.datetime.now()
    for location in search_history:
        # Retrieve JSON data by generating API url based on lat/lon
        lat = float(locator(location[0], location[1])["lat"])
        lon = float(locator(location[0], location[1])["lon"])
        current_weather_lat_lon = "lat=" + str(round(lat,2)) + "&lon=" + str(round(lon,2))
        units = "&units=imperial"
        current_coord_weather_url = API_endpoint + current_weather_lat_lon + join_1 + API_key + units
        # Convert JSON data into Python dict type, and store it in weather[] list
        json_data = requests.get(current_coord_weather_url).json()
        weather_data = json.loads(json.dumps(json_data))
        weather.append(weather_data)
    return render_template("weather.html", length=len(search_history), search_history=search_history, weather=weather, current_time=current_time)

@app.route("/timeplace", methods=["GET", "POST"])
@login_required
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
            cur1.execute("INSERT INTO timeplaces (username, zipcode, country, requesttime, timestamp) VALUES (?, ?, ?, ?, ?)", (session["username"], zipcode, nation, requesttime, timestamp))
            userdata_db.commit()
            return redirect(url_for('skymap'))
        else:
            return render_template("timeplace.html", message=message, months=months, nations=nations, present_month=datetime.datetime.now().strftime('%B'), present_day=int(datetime.datetime.now().strftime('%d')), present_year=datetime.datetime.now().strftime('%Y'), present_hour=datetime.datetime.now().strftime('%H'), present_minute=datetime.datetime.now().strftime('%M'))

# Called only from /skymap route to generate skymap image using matplotlib
# Found useful information on https://stackoverflow.com/questions/50728328/python-how-to-show-matplotlib-in-flask
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
@login_required
def skymap():
    # Renders skymap labeled with location and time
    for item in cur1.execute("SELECT * FROM timeplaces ORDER BY timestamp DESC LIMIT 1"):
        lat = round(float(locator(item[1], item[2])["lat"]), 3)
        lon = round(float(locator(item[1], item[2])["lon"]), 3)
        zipcode = item[1]
        country = item[2]
        time = item[3][0:-3]
        return render_template("skymap.html", lat=lat, lon=lon, zipcode=zipcode, country=country, time=time)


# The following three functions were originally intended to be in helpers.py, but they were ultimately placed
# in application.py to avoid the error: mathplotlib GUI is not in main thread


# Draw polar graph to produce template for sky map
def draw_template():
    # Basic configurations
    fig = matplotlib.pyplot.figure(dpi=500)
    ax = fig.add_axes([0, 0, 1, 1], polar=True)
    ax.set_theta_direction(-1)  
    ax.set_theta_zero_location('N')

    # Hide unnecessary tick labels
    for xlabel in ax.get_xticklabels():
        xlabel.set_visible(False)
    for ylabel in ax.get_yticklabels():
        ylabel.set_visible(False)
    
    # Draw inner gridlines
    ax.grid(True)
    gridlines = ax.get_xgridlines() + ax.get_ygridlines()
    for line in gridlines:
        line.set_linewidth(0.2)
        line.set_linestyle('-')
    
    return fig,ax


# Draw constellations onto skymap using data from stars.db and constellations.db
def draw_constellations(ax):
    # Generate list of all constellations
    constellations = []
    for item in c.execute("SELECT DISTINCT(constellation) FROM constellations"):
        constellations.append(item[0])
    # Draw each constellation by pairs of stars, using their right ascensions and declinations as coordinates
    for constellation in constellations:
        constellation_path = []
        for item in c.execute("SELECT * FROM constellations WHERE constellation=? ORDER BY ord", (constellation,)):
            constellation_path.append(item[1])
            for i in range(len(constellation_path) - 1):
                stars = []
                ras = []
                decs = []
                for j in [i, i+1]:
                    stars.append(constellation_path[j])
                    for item in s.execute("SELECT ra FROM stars WHERE constellation = ? AND star = ?", (constellation, stars[j-i])):
                        ras.append(item[0])
                    for item in s.execute("SELECT dec FROM stars WHERE constellation = ? AND star = ?", (constellation, stars[j-i])):
                        decs.append(item[0])
                ax.plot(numpy.radians([ras[0], ras[1]]), [-1 * decs[0]+45, -1 * decs[1] + 45], linewidth=1.0, color='skyblue')
                # Add label with constellation name next to first star 
                if i == 0:
                    ax.text(numpy.radians(ras[0]), -1 * decs[0]+45, str(format(constellation)), fontsize=4, weight='bold')

# Draw area of skymap that observer can see
# Found useful documentation on https://matplotlib.org/3.3.3/users/whats_new.html#what-s-new-in-matplotlib-3-3-0 
def draw_vision(ax, input_time, input_loc):
    # Convert coordinates to altitude-azimuth coordinates and to right-ascension/declination coordinates
    azimuth = numpy.arange(0, 360.1, 1)
    altitude = numpy.zeros(len(azimuth))
    vision = SkyCoord(azimuth, altitude, frame='altaz', unit='deg', obstime=input_time, location=input_loc).transform_to('icrs')
    
    # Plot RA and DEC coordinates
    ax.plot(vision.ra.radian, -vision.dec.value+45, '-', linewidth=0.3, color='darkblue')
    
    # Fill in outside circle
    ax.fill_between(vision.ra.radian, -vision.dec.value+45, len(-vision.dec.value+45) * [90], where=len(-vision.dec.value+45) * [90]>=-vision.dec.value+45, facecolor='skyblue', alpha=0.8 )

    # Draw curved axis
    curved_alt = [num for num in numpy.arange(0, 90.1, 1)]
    curved_az = len(curved_alt)*[90] + (len(curved_alt)-1)*[270]
    curved_alt = curved_alt + curved_alt[:-1][::-1]
    curved_ax = SkyCoord(curved_az, curved_alt, frame='altaz', unit='deg', obstime=input_time, location=input_loc).transform_to('icrs')
    ax.plot(curved_ax.ra.radian, -curved_ax.dec.value+45, '-', linewidth=0.5, color='turquoise')

    # Draw straight axis
    straight_ax = SkyCoord([0, 180], [0, 0], unit='deg', frame='altaz', obstime=input_time, location=input_loc).transform_to('icrs')
    ax.plot(straight_ax.ra.radian, -straight_ax.dec.value+45, '-', linewidth=0.5, color='turquoise')

    # Label North, South, East, West
    directions = ['N', 'E', 'S', 'W']
    counter = 0
    vision_circle_deg = SkyCoord(numpy.arange(0, 345.1, 15), numpy.zeros(len(numpy.arange(0, 345.1, 15))), frame='altaz', unit='deg', obstime=input_time, location=input_loc).transform_to('icrs')
    for (coordinate, label) in zip(vision_circle_deg, numpy.arange(0, 345.1, 15)):
        if int(label) % 90 == 0:
            ax.text(coordinate.ra.radian, -coordinate.dec.value+45, directions[counter], fontname="serif", fontsize=10, fontweight='bold' )
            counter += 1

# Draw location of moon at input time
def draw_moon(ax, input_time, input_loc):
    moon = get_moon(time=input_time, location=input_loc)
    moon = SkyCoord(moon.ra, moon.dec, frame='gcrs').transform_to('icrs')
    ax.plot([moon.ra.radian], [-moon.dec.value+45], color='yellow', linestyle='', marker='o')