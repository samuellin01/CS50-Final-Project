import os
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
from geopy.geocoders import Nominatim
from iso3166 import countries

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
