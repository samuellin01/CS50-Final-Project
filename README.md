# CS50-Final-Project

Note that GitHub won't let you upload empty files! 

Linux Instructions:

To clone this repository:
`git clone git@github.com:samuellin01/CS50-Final-Project.git`

To pull from this repository:
1) cd into the CS50-Final-Project directory
2) type: `git pull`

To commit changes to the repository:
1) cd into the CS50-Final-Project directory
2) Run `git status` to see all the files that you've changed locally.
3) Run `git add -A`, then `git commit -m "<substitute a name for your commit>".` It should produce with something like [main f0efce8] ...
4) Git might ask you to sign in into Github.
5) Run `git push`
6) Go to github online and check if it actually worked.

Before running Flask on your local IDE (such as VSCode):
1) If it says `ModuleNotFoundError: No module named 'cs50'`, run `pip install cs50` or `pip3 install cs50`
2) If it says `ModuleNotFoundError: No module named 'flask_session'`, run `pip install Flask-Session`
3) Also, pip install any other APIs that we end up using

To run Flask on your local IDE:
1) Run `export FLASK_APP=application`
2) Run `export FLASK_ENV=development`
3) Run `flask run`
If it works, the IDE will provide you with a local IP address, which you can copy/paste into your browser.
