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

If it says `ModuleNotFoundError: No module named ...`, run `pip install -r requirements.txt`(or pip3)

To run Flask on your local terminal:
1) Run `export FLASK_APP=application`
2) Run `export FLASK_ENV=development`
3) Run `flask run`
If it works, the IDE will provide you with a local IP address, which you can copy/paste into your browser.

Note: Sometimes, because of cache, the IDE will automatically run an older version of the flask application, so some changes may not be reflected. To avoid this, use Incognito Mode.
