import pickle
import numpy as np
import pandas as pd
import pymysql as mdb

## Save match stats of each team to database

# Create database teamData
teamData = pickle.load(open('../data/teamClean.p', "rb"))
con = mdb.connect(host = "localhost", user = "root", passwd = "000000")
cursor = con.cursor()
sql_drop = "DROP DATABASE IF EXISTS teamData"
sql_create  = 'CREATE DATABASE teamData'
cursor.execute(sql_drop)
cursor.execute(sql_create)
con.close()

# Put data into the database
con = mdb.connect('localhost', 'root', '000000', 'teamData') #host, user, password, #database
with con:
    for ii in teamData:
        tName = ii.replace(' ', '_')
        print tName
        teamData[ii].to_sql(con = con, name = tName, if_exists = 'replace', flavor = 'mysql')



