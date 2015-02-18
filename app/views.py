from flask import render_template, request
from app import app
import pickle
import pymysql as mdb
from PredictMatchAll import *

@app.route('/')
@app.route('/input')
def input():
    # Load team names
    try:
        # Load config file for database 
        app.config.from_pyfile("../aws.cfg")
        db = mdb.connect(user = app.config['DB_USER'], host = app.config['DB_HOST'], 
        passwd = app.config['DB_PASS'], db = app.config['DB_NAME'], charset = 'utf8')
        cur = db.cursor()
        cur.execute("show tables;")
        query_results = cur.fetchall()
        teams = [ii[0].replace('_', ' ').title() for ii in query_results]
    except Exception as e:
        print e.message
        text_file = open("error1.txt", "a")
        text_file.write(e.message)
        text_file.close()
        #trying to reconnect

    return render_template("input.html", title = 'Home', teams = teams)
	
@app.route('/output', methods = ['GET'])
def output():
    # pull user selected teams
    yourName = request.args.get('Item_1')
    tgtName = request.args.get('Item_2')

    # Load team models
    teamModels = pickle.load(open('./data/teamModels.p', "rb")) # teamModels contain log models for all teams

    # Compute chance of winning and recommended actions
    try:
        # Load config file for database 
        app.config.from_pyfile("../aws.cfg")
        db = mdb.connect(user = app.config['DB_USER'], host = app.config['DB_HOST'], passwd = app.config['DB_PASS'], db = app.config['DB_NAME'], charset = 'utf8')
        odds, oddsNew, actions = PredictMatch(yourName, tgtName, teamModels, db)
    except Exception as e:
        print e.message
        text_file = open("error2.txt", "a")
        text_file.write(e.message)
        text_file.write('yourName: ' + yourName + ' tgtName: ' + rgtName)
        text_file.close()  
    teamRec = {'yourName': yourName, 'tgtName': tgtName, 'odds': odds, 'oddsNew': oddsNew, 'actions': actions}
    return render_template("output.html", title = 'Home', teamRec = teamRec)

@app.route('/contact')
def contact():
	return render_template("contact.html")

@app.route('/demo')
def demo():
	return render_template("demo.html")