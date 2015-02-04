# module for comparing stats and making recommendataions
"""
Read team names from user input, retrieve features of teams from MySQL DB, compute odds of winning and recommend features to care
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymysql as mdb

def FeatureImprove(tgtName, yourName):
    con = mdb.connect('localhost', 'root', '000000', 'data') #host, user, password, #database
    with con:
        cur = con.cursor()
        #cur.execute("drop table you_rtablename")
        featureAPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + tgtName.replace(' ', '_') + '_featureRanked', con = con)
        featureBPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + yourName.replace(' ', '_') + '_featureRanked', con = con)
        teamAPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + tgtName.replace(' ', '_'), con = con)
        teamBPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + yourName.replace(' ', '_'), con = con)
        #df2 = pd.io.sql.read_sql(sql = "SELECT * FROM yourtablename", con = con)

    # Get stats of Team A's win and lose matches
    featureA = list(featureAPipe['index'][:10])
    dfA = teamAPipe.ix[:, ['y'] + featureA]
    aWin = dfA[dfA['y'] == 1]
    aLose = dfA[dfA['y'] == 0]

    # Get stats of Team B: Revert the features of A to retrieve features
    featureB = []
    for ii in featureA:
        if '_op' in ii:
            featureB.append(ii[:-3])
        else:
            featureB.append(ii + '_op')
    dfB = teamBPipe.ix[:, ['y'] + featureB]
    # Revert again so I'll be comparing A's opponent's with B, and A with B's opppoent
    # e.g. pass_op in dfB is actually pass for B
    dfB.columns = [['y'] + featureA] 
    
    # Get max of stats of both dfA and dfB for normalization
    maxStats = dfA.append(dfB).describe().ix['max', 1:11]

    # Get mean stats for Team A's win and lose matches; and Team B's all matches
    meanAWin = aWin.describe().ix['mean', 1:11]
    meanALose = aLose.describe().ix['mean', 1:11]
    meanB = dfB.describe().ix['mean', 1:11]

    # Get similarity of Team B's match to Team A's win and lose matches and compare
    AwinSim = np.sqrt(((meanB - meanAWin) ** 2 / maxStats ** 2).sum())
    BwinSim = np.sqrt(((meanB - meanALose) ** 2 / maxStats ** 2).sum())

    ratioBWin = (1 / BwinSim) / ((1 / AwinSim) + (1 / BwinSim)) # The smaller BwinSim, the larger Chance B wins

    # Get difference of match features and recommend features to focus on
    diffB2ALose = meanB / maxStats - meanALose / maxStats

    return ratioBWin, diffB2ALose

def PredictWin(tgtName, yourName):
    ratioBWin, diffB2ALose = FeatureImprove(tgtName, yourName)
    ratioBWinRev, diffB2ALoseRev = FeatureImprove(yourName, tgtName)
    odds = (ratioBWin + 1 - ratioBWinRev) / 2
    print "The odds of your team winning is " + str(odds) 
    
    return diffB2ALose, odds

def MakeRecommendation(diffB2ALose):
    absDf = diffB2ALose.abs()
    absDf.sort(ascending = False)   

    featureB = []
    featureB_op = []
    for ii in absDf.index:
        if "_op" in ii:
            featureB.append(ii)
        else:
            featureB_op.append(ii)
    
    print "To increase Your Team's odds of winning:"

    yourTeamAct = []
    for ii in featureB:
        printII = ii[:-3]
        #if diffB2ALose[ii] > 0:
        #    print "You may want to have less " + printII
        if diffB2ALose[ii] < 0:
            print "You want to have more " + printII
            yourTeamAct.append(printII)

    tgtTeamAct = []
    for ii in featureB_op:
        printII = ii
        if diffB2ALose[ii] > 0:
            print "Be careful of Target Team's " + printII
            tgtTeamAct.append(printII)
        #if diffB2ALose[ii] < 0:
        #   print "Allow the Target Team to have more " + printII

    return yourTeamAct, tgtTeamAct


def TmpMain(tgtName, yourName):
    diffB2ALose, odds = PredictWin(tgtName, yourName)
    yourTeamAct = []
    tgtTeamAct = []
    if tgtName != yourName:
        yourTeamAct, tgtTeamAct = MakeRecommendation(diffB2ALose)

    return round(odds, 2), yourTeamAct, tgtTeamAct

#TmpMain('Real Madrid', 'Atletico Madrid')
