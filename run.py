#!/usr/bin/env python
from app import app
import pymysql as mdb
import pickle

# Load config file for database
app.config.from_pyfile("aws.cfg")

## Load some data here before users hit the website

# Load the database: was in views
app.db = mdb.connect(user = app.config['DB_USER'], host = app.config['DB_HOST'], 
	passwd = app.config['DB_PASS'], db = app.config['DB_NAME'], charset = 'utf8')

# Load team names: was in views - input()
cur = app.db.cursor()
cur.execute("show tables;")
query_results = cur.fetchall()
app.teams = [ii[0].replace('_', ' ').title() for ii in query_results]

# Load team models: was in views - output()
app.teamModels = pickle.load(open('./data/teamModels.p', "rb")) # teamModels contain log models for all teams

if __name__ == "__main__":
    app.run(debug = True, host = '0.0.0.0', port = 80)
