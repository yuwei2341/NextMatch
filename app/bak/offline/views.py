from flask import render_template, request
from app import app
import pymysql as mdb
from PredictMatchAll import *

db = mdb.connect(user="root", host="localhost", passwd = '000000', db="teamData", charset='utf8')

@app.route('/')
@app.route('/input')
def input():
	cur = db.cursor()
	cur.execute("show tables;")
	query_results = cur.fetchall()
	teams = [ii[0].replace('_', ' ').title() for ii in query_results]
	return render_template("input.html", title = 'Home', teams = teams)
	
@app.route('/output', methods = ['GET'])
def output():
    #pull 'ID' from input field and store it
    yourName = request.args.get('Item_1')
    tgtName = request.args.get('Item_2')

    teamModels = pickle.load(open('../data/teamModels.p', "rb")) # teamModels contain log models for all teams
    odds, oddsNew, actions = PredictMatch(yourName, tgtName, teamModels, db) 

    teamRec = {'yourName': yourName, 'tgtName': tgtName, 'odds': odds, 'oddsNew': oddsNew, 'actions': actions}
    #print teamRec 
    return render_template("output.html", title = 'Home', teamRec = teamRec)
