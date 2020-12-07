import os
# import requests (will use with api later)
import urllib.parse
import sqlite3
import matplotlib.pyplot as plt
import numpy

from flask import redirect, render_template, request, session
from functools import wraps
from geopy.geocoders import Nominatim
from iso3166 import countries
from astropy.coordinates import SkyCoord, get_moon

stars_db = sqlite3.connect("stars.db", check_same_thread=False)
constellations_db = sqlite3.connect("constellations.db", check_same_thread=False)
s = stars_db.cursor()
c = constellations_db.cursor()

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# locator() takes in zipcode & country, outputs a dict with location data or None if nonexistent location
def locator(zipcode, country):
    geolocator = Nominatim(user_agent="skymap")
    country_symbol = countries[country].alpha2.lower()
    location = geolocator.geocode(zipcode, country_codes=country_symbol)
    if location == None:
        return location
    else:
        return location.raw

# Draw polar graph to produce template for sky map
def draw_template():
    # Basic configurations
    fig = plt.figure(dpi=500)
    ax = fig.add_axes([0, 0, 1, 1], polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)  

    # Draw inner gridlines
    ax.grid(True)
    gridlines = ax.get_xgridlines() + ax.get_ygridlines()
    for line in gridlines:
        line.set_linestyle(':')
        line.set_linewidth(0.2)
    
    # Hide unnecessary tick labels
    for yticklabel in ax.get_yticklabels():
        yticklabel.set_visible(False)
    for xticklabel in ax.get_xticklabels():
        xticklabel.set_visible(False)
    return fig,ax

def draw_constellations(ax):
    constellations = []
    for item in c.execute("SELECT DISTINCT(constellation) FROM constellations"):
        constellations.append(item[0])
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
                ax.plot(numpy.radians([ras[0], ras[1]]), [-1 * decs[0]+45, -1 * decs[1] + 45], color='skyblue', marker=None, linewidth=1.0)
                if i == 0:
                    ax.text(numpy.radians(ras[0]), -1 * decs[0]+45, "{}".format(constellation), fontsize=4, weight='bold' )

def plot_vision(ax, obs_time, obs_loc):
    """
    Plot current field-of-view (FOV)
    """

    # coordinates of field-of-view-circle' points in (alt,az) frame
    fov_az = numpy.arange(0, 360+0.1, 1)
    fov_alt = numpy.zeros(len(fov_az))
    fov = SkyCoord(fov_az, fov_alt, unit='deg', frame='altaz', obstime=obs_time, location=obs_loc)
    # converting this coordinates to (RA,dec) format for plotting them onto plot
    fov = fov.transform_to('icrs')
    # plotting field-of-view circle
    ax.plot(fov.ra.radian, -fov.dec.value+45, '-', linewidth=0.3, color='darkblue')

    # fill the area that we cannot observe now
    shared_ax = fov.ra.radian
    fov_circle = -fov.dec.value+45
    outer_circle = len(fov_circle) * [-(-45)+45]
    ax.fill_between( shared_ax, fov_circle, outer_circle, where=outer_circle>=fov_circle,
                     facecolor='skyblue', alpha=0.8 )

    #
    # putting on plot ticks of circle axis (axis of azimuth) in the same way as outer circle
    #
    fov_ticks_az = numpy.arange(0, 345+0.1, 15)
    fov_ticks_alt = numpy.zeros(len(fov_ticks_az))
    fov_ticks = SkyCoord( fov_ticks_az, fov_ticks_alt, unit='deg', frame='altaz',
                          obstime=obs_time, location=obs_loc )
    fov_ticks = fov_ticks.transform_to('icrs')
    cardinal_directions = ['N', 'E', 'S', 'W']  # anti-clockwise
    cnt = 0
    for (tick_coord, label) in zip(fov_ticks, fov_ticks_az):
        if int(label) % 90 == 0:
            ax.text( tick_coord.ra.radian, -tick_coord.dec.value+45,
                     cardinal_directions[cnt], fontsize=10,
                     fontname="serif", fontweight='bold' )
            cnt += 1

    #
    # plot straight axis - from South to North - of field of view circle (similarly)
    #
    SN_ax_alt = [0, 0]
    SN_ax_az = [0, 180]
    SN_ax = SkyCoord( SN_ax_az, SN_ax_alt, unit='deg', frame='altaz',
                      obstime=obs_time, location=obs_loc )
    SN_ax = SN_ax.transform_to('icrs')
    ax.plot(SN_ax.ra.radian, -SN_ax.dec.value+45, '-', linewidth=0.5, color='lightseagreen')

    #
    # plot curved axis - from West to East - of field of view circle (similarly)
    #
    WE_ax_alt = [alt for alt in numpy.arange(0, 90+0.1, 1)]
    WE_ax_az = len(WE_ax_alt)*[90] + (len(WE_ax_alt)-1)*[270]
    WE_ax_alt = WE_ax_alt + WE_ax_alt[:-1][::-1]
    WE_ax = SkyCoord (WE_ax_az, WE_ax_alt, unit='deg', frame='altaz',
                     obstime=obs_time, location=obs_loc )
    WE_ax = WE_ax.transform_to('icrs')
    ax.plot(WE_ax.ra.radian, -WE_ax.dec.value+45, '-', linewidth=0.5, color='lightseagreen')

def plot_moon(ax, obs_time, obs_loc):
    """
    Put Moon on a given Axes instance
    """

    moon = get_moon(obs_time, location=obs_loc)
    moon = SkyCoord(moon.ra, moon.dec, frame='gcrs').transform_to('icrs')

    ax.plot( [moon.ra.radian], [-moon.dec.value+45], label='Moon', linestyle='',
             color='yellow', marker='$🌛$')