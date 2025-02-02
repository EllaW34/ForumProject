from flask import Flask, flash, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
import pymongo
from pymongo import InsertOne, DeleteOne, ReplaceOne
import os
import sys
import pprint
from bson.objectid import ObjectId
from datetime import date, time, datetime


connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]
    
client = pymongo.MongoClient(connection_string)
db = client[db_name]
collection = db['DronesCollection'] #1. put the name of your collection in the quotes
    
app = Flask(__name__)

app.debug = True #Change this to False for production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)


#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out.')
    return redirect('/')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        flash('Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args), 'error')
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            flash('You were successfully logged in as ' + session['user_data']['login'] + '.')
        except Exception as inst:
            session.clear()
            print(inst)
            flash('Unable to login, please try again.  ', 'error')
    return redirect('/')

@app.route('/newPost', methods=['GET', 'POST'])
def renderNewPost():
    print("test")
    if request.method == 'POST':
        username = pprint.pformat(session["user_data"]["login"])
        today = date.today()
        today = today.strftime("%m/%d/%Y")
        title = request.form["title"]
        text = request.form["text"]
        
        post = {"username": username[1:-1], "date": str(today), "title": title, "text": text}
        collection.insert_one(post)
    return redirect('/page1')

@app.route('/page1', methods=['GET', 'POST'])
def renderPage1():
    session["posts"] = ""    
    session["list"] = []
    for doc in collection.find():
        number = len(session["list"])
        session["list"].append("<div id=\"post\"><p>" + doc["username"] + "</p><p>" + doc["date"] + "</p><p id=\"title\">" + doc["title"] + "</p><p id=\"words\">" + doc["text"] + "</p><button type=\"button\" id=\"" + str(doc["_id"]) + "\">Reply</button><div id=\"" + str(doc["_id"]) + "-Hide" + "\" class=\"hidden\"><br><br><textarea name=\"text\" rows=\"10\" cols=\"114\" required></textarea></div><br></div><br>")
    for new in session["list"]:
        session["posts"] += Markup(new)
    return render_template('page1.html')

@app.route('/addPost')
def renderAddPost():   
    return render_template('addPost.html')
    
@app.route('/reply')
def renderReply():
    #print("test")
    #position = request.args["position"]
    #print(position)
    #print(collection.find_one({"_id": ObjectId(position)})["username"])
    #session["list"[position]] = "<div id=\"post\"><p>" + collection.find_one({"_id": ObjectId(position)})["username"] + "</p><p>" + collection.find_one({"_id": ObjectId(position)})["date"] + "</p><p id=\"title\">" + collection.find_one({"_id": ObjectId(position)})["title"] + "</p><p id=\"words\">" + collection.find_one({"_id": ObjectId(position)})["text"] + "</p><form action=\"/reply\"><input type=\"hidden\" id=\"reply\" name=\"position\" value=\"" + str(collection.find_one({"_id": ObjectId(position)})["_id"]) + "\"><input type=\"submit\" action=\"/reply\" id=\"reply\" value=\"Reply\"></form><div><br><br><textarea name=\"text\" rows=\"10\" cols=\"114\" required></textarea></div><br></div><br>"
    #print(session["list"[position]])
    return redirect("/page1")

@app.route('/googleb4c3aeedcc2dd103.html')
def render_google_verification():
    return render_template('googleb4c3aeedcc2dd103.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']


if __name__ == '__main__':
    app.run()
