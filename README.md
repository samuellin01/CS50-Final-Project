Link to Youtube video: https://youtu.be/2tBjOh42LVc 

File Organization:

Our final project is a Flask application. Its components include various Python, HTML, CSS, and SQL files, organized such that the HTML files are located in a templates folder with the index.html as the homepage with the search history and the rest of the HTML corresponding to their function. We also have a static folder containing the CSS file and an image for our favicon.

Before running the Flask application:

First, download and unzip the folder titled CS50-Final-Project-main. Our flask application can be executed either in a computer’s terminal, or in CS50 IDE. Regardless of which method is used, a user must have already navigated to the location of CS50-Final-Project-main on their computer’s directory. Once this is done, run the following command:
`> pip install -r requirements`
If this command returns an error, it is probably because the computer has a different version of pip installed. Run the following command instead:
`> pip3 install -r requirements`
This should install all of the necessary modules needed to run the program. It is best to do this with an Internet connection.


Running the Flask application:

To run the Flask application on Unix Bash (Linux, Mac, etc.), type the following commands:
`$ export FLASK_APP=application`
`$ flask run`
To run the Flask application on Windows CMD, type the following commands:
`> set FLASK_APP=application`
`> flask run`
To run the Flask application on Windows Powershell, type the following commands:
`> $env:FLASK_APP = "application"`
`> flask run`
To run the Flask application on CS50 IDE, type the following command:
`> flask run`
The flask application should run properly at this point. Something similar to this should appear:
`$ flask run`
 `* Serving Flask app "application"`
 `* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)`
The flask application can then be run on any browser (although Google Chrome works most reliably) by typing in the above address into the browser’s address bar. 




A Note about Incognito Mode:

This usually does not happen, but sometimes, a browser will store cache for the Flask website. This is usually only a problem on the developer’s side, but if changes in session are not reflected properly, then stop the flask application and rerun it in Incognito Mode.

Navigating our Flask Website:

Once you have our skymap site open, you should see the interactive sky map sign in page with the title at the top and nav bar on the left hand side. If you are a first time user, you should click the register button in the nav bar to register. 

Once your username and password have been accepted, then you’ll be at the home screen with the search history. If you are a first time user, this shouldn’t have any information just yet. Hop on over to the sky map section in the nav bar where you’ll see several pieces of information to fill out regarding your location and time. The main location info will be the zip code and for ease of use, we have defaulted the time to the user’s current time. After submitting this info, a sky map will load that is calibrated to what you will see in the night sky from your location and time. This may take several seconds to load. 

Next, we also have our weather section which will display the weather in local time for the locations entered in the sky map which appear in the search history. This will provide the user with the necessary information to determine if conditions are right for stargazing. We hope you enjoy our website and grow your interest in astronomy!

Now, when you’re done viewing the website you can sign out by simply clicking the sign out button. Make sure you do this after you’re done as this will keep your location information safe. 
