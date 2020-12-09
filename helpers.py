import os
import urllib.parse
import sqlite3
import matplotlib.pyplot as plt
import numpy
import logging

from flask import redirect, render_template, request, session
from functools import wraps
from geopy.geocoders import Nominatim
from iso3166 import countries
from astropy.coordinates import SkyCoord, get_moon

# Turn off matplotlib debug log messages
logging.basicConfig()
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

# Initialize stars and constellations SQL databases
stars_db = sqlite3.connect("stars.db", check_same_thread=False)
constellations_db = sqlite3.connect("constellations.db", check_same_thread=False)
s = stars_db.cursor()
c = constellations_db.cursor()

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
        line.set_linestyle(':')
    
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
                    ax.text(numpy.radians(ras[0]), -1 * decs[0]+45, "{}".format(constellation), fontsize=4, weight='bold')

# Draw area of skymap that observer can see
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
    moon = get_moon(input_time, location=input_loc)
    moon = SkyCoord(moon.ra, moon.dec, frame='gcrs').transform_to('icrs')
    ax.plot([moon.ra.radian], [-moon.dec.value+45], color='yellow', linestyle='', marker='$🌛$')