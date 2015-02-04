from flask import render_template, request
from app import app
import pymysql as mdb
from PredictMatch import *

db = mdb.connect(user="root", host="localhost", passwd = '000000', db="data", charset='utf8')

@app.route('/')
@app.route('/index')
def index():
    with db:
        cur = db.cursor()
        cur.execute("show tables;")
        query_results = cur.fetchall()       
        teams = [ii[0] for ii in query_results if 'featureranked' not in ii[0]]
    return render_template("index.html", title = 'Home', user = { 'nickname': 'Miguellll' , 'teams': teams})

@app.route('/results', methods = ['POST'])
def cities_page():
	"""
    yourName = request.form['Item_1']
    tgtName = request.form['Item_2']
    odds, yourTeamAct, tgtTeamAct = TmpMain(tgtName, yourName)
    print yourTeamAct
    tgtTeamAct = [ii for ii in tgtTeamAct if "accura" not in ii]
    return render_template("results.html",
       title = 'Home', teamRec = {'teamName': [yourName, tgtName], 'odds': odds, 'actions': [yourTeamAct, tgtTeamAct]})
	"""

@app.route('/index_fancy')
def cccities_page():
    with db:
        cur = db.cursor()
        cur.execute("show tables;")
        query_results = cur.fetchall()       
        teams = [ii[0] for ii in query_results if 'featureranked' not in ii[0]]
    return render_template("index_fancy.html", title = 'Home', user = { 'nickname': 'Miguellll' , 'teams': teams})

@app.route('/input')
def cities_input():
	teams = 'asdf'
	return render_template("input.html", teams = teams)

@app.route('/output', methods = ['POST'])
def cities_output():
  #pull 'ID' from input field and store it
  yourName = request.form['Item_1']
  tgtName = request.form['Item_2']
  #team = request.args.get('ID')
  team2 = '2'
  print yourName
  
  return render_template("output.html", yourName = yourName, team = team2, the_result = team2)
