from flask import render_template, request
from flask import current_app
from app import app
from PredictMatchAll import *


@app.route('/')
@app.route('/input')
def input():
	return render_template("input.html", title = 'Home', teams = current_app.teams)
	
@app.route('/output', methods = ['GET'])
def output():
    try:
        # pull user selected teams
        yourName = request.args.get('Item_1')
    	tgtName = request.args.get('Item_2')

    	# Compute chance of winning and recommended actions
    	odds, oddsNew, actions = PredictMatch(yourName, tgtName, current_app.teamModels, current_app.db) 
    	print odds
    	teamRec = {'yourName': yourName, 'tgtName': tgtName, 'odds': odds, 'oddsNew': oddsNew, 'actions': actions}
    except Exception as e:
        print str(e)
    return render_template("output.html", title = 'Home', teamRec = teamRec)

@app.route('/contact')
def contact():
	return render_template("contact.html")

@app.route('/demo')
def demo():
	return render_template("demo.html")