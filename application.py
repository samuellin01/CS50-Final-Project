import os
import datetime
 
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.route("/")
def index():
    return render_template("layout.html");

#testing git commit

#layout deadline: 11/27 end of day

#pages for different constellations (redirected from homepage) 11/28 (both work on it)

#sign in page (M) 11/30

#register (M) 11/30

#form for user to input location, time, etc. (S) 11/30

#

#due 11/30
