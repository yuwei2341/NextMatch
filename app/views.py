from flask import render_template, request
from app import app
import pickle
from PredictMatchAll import *

# Load config file for database
app.config.from_pyfile("../aws.cfg")
# Load the database
db = mdb.connect(user = app.config['DB_USER'], host = app.config['DB_HOST'], 
    passwd = app.config['DB_PASS'], db = app.config['DB_NAME'], charset = 'utf8')

@app.route('/')
@app.route('/input')
def input():
    # Load team names
    cur = db.cursor()
    cur.execute("show tables;")
    query_results = cur.fetchall()
    teams = [ii[0].replace('_', ' ').title() for ii in query_results]
    return render_template("input.html", title = 'Home', teams = teams)
	
@app.route('/output', methods = ['GET'])
def output():
    # pull user selected teams
    yourName = request.args.get('Item_1')
    tgtName = request.args.get('Item_2')

    # Load team models
    teamModels = pickle.load(open('./data/teamModels.p', "rb")) # teamModels contain log models for all teams

    # Compute chance of winning and recommended actions
    odds, oddsNew, actions = PredictMatch(yourName, tgtName, teamModels, db) 
    teamRec = {'yourName': yourName, 'tgtName': tgtName, 'odds': odds, 'oddsNew': oddsNew, 'actions': actions}

    return render_template("output.html", title = 'Home', teamRec = teamRec)

@app.route('/contact')
def contact():
	return render_template("contact.html")

@app.route('/demo')
def demo():
	return render_template("demo.html")