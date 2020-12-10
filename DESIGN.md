Layout

We decided to implement Bootstrap’s functionality for our left navbar and overall design. Instead of the horizontal navbar that we commonly saw used, we opted for a vertical one that would provide a cleaner look and provide more space for our features. Colors were used that matched the theme of our project which was to implement a working night sky for each user. Another key note is that we created an HTML template with the intention of using Jinja, so that we wouldn’t have to copy and paste the same html for each page. 

Register

To personalize the experience of our website for each unique visitor, we stored each user and password in a SQLite database. We used similar code from the finance pset such as the HTML/Python to simulate this functionality. On the front end of the website, the user had to input a username and password and reconfirm the password. On the back end of the website, we checked against restraints: for example, the username had to be unique so that we could track each user, and the passwords had to match.  We had to additionally place links to these routes in the HTML navbar so that users can navigate to these pages. 

Signin / Signout

This was important so that not just anyone could access our website without providing information. We also kept track of the session_id so that each user can see their own search history and not have their location be broadcast to all users. It was important to us that location privacy was maintained in our website. More evidence of our personalization was that we added another feature that showed on the left navbar which person was signed in. 

Skymap

Our original intention for this final project was to produce an interactive sky map for a user based on a specific location and time. To implement this, we created an HTML form to retrieve the location and time, two pieces of data that had to be processed on the back end of the website. To process location, we used Geopy API to convert zipcode and country into latitude and longitude coordinates. To process time, we used python’s datetime module. We found many APIs online that could produce the coordinates of celestial objects (in right-ascension/declination coordinates) given a user’s location and time, but we struggled to find an API that could produce an interactive graphic that had our desired results. 

Instead, we decided to use matplotlib API to draw out the constellations based on these coordinates. To do this, we pulled data from SIMBAD, a public astronomy database, converting their CSV databases into SQLite databases first. With the right-ascension/declination coordinates for individual stars in constellations, we could then plot them onto a polar graph in pairs. Finally, we used Astropy API to identify the portion of the sky observable by a user, and plotted this area on the same graph in a different color. We used North/South/East/West markers so that users could apply our graphic to real life. FInally, we rendered this graphic into a PNG file attached to one of our HTML pages.

Search History

Again, similar to finance, we have a search history of the user which is nice to have as you can look back on which locations you looked at and at what times to look up those skymaps from the past so that you can compare with the future. We had a table in the HTML and also used Jinja to pull data from our database containing this information. This was relatively easy to implement because every search made by a user was recorded in a SQLite database.

Weather 

Our original intention was to provide a weather forecast widget alongside the sky map, both of which were to be based on the same location and time inputs. We encountered a design obstacle upon trying to implement this: most free weather APIs on the Internet can only provide forecasts up to three days prior and after the current time. This was a problem because we had designed our sky map to work for dates in a 40 year time span, and in fact, it would be a huge downgrade for us to limit users to a mere 6 day time span. Instead, we decided to work around this by providing only the current weather forecast for locations in a user’s search history. This worked out, and our current implementation provides current temperature, apparent temperature, wind speed, and a description of the current weather.

Additional Notes

We structured our Flask code into an application.py file and a helpers.py file, with most functions located in application.py. We had originally intended to place all functions without route decorators in helpers.py to avoid clutter, but this did not work out because matplotlib would occasionally stop working, saying that the matplotlib GUI must be in the main thread. Furthermore, we used Python’s sqlite3 module instead of CS50’s SQL library because we found that sqlite3 could execute reliably more often than CS50 SQL. 
