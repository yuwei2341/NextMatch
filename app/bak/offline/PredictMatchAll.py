# module for comparing stats and making recommendataions
"""
Read team names from user input, retrieve features of teams from MySQL DB, compute odds of winning and recommend features to care
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymysql as mdb
from sklearn import linear_model 
import pickle

def QueryTeamData(tgtName, yourName, db):
	"""
	Get data from MySQL DB
	"""
	cur = db.cursor()
	teamTgtPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + tgtName.replace(' ', '_'), con = db)
	teamYourPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + yourName.replace(' ', '_'), con = db)
	return teamTgtPipe, teamYourPipe        

def PredictOp(teamTgtPipe, teamYourPipe, tgtName, teamModels):

    coef = teamModels[tgtName]

    # Get stats of Team A's win and lose matches - only 20 features are saved
    features = list(coef['features'])
    # Get stats of Team B: Revert the features of A to retrieve features for B
    featureYour = []
    featureTgt = []
    for ii in features:
        if '_op' in ii:
            featureYour.append(ii[:-3])
        else:
            featureTgt.append(ii)

    dfTgt = teamTgtPipe[teamTgtPipe['season'] == 1415].ix[:, featureTgt]
    dfYour = teamYourPipe[teamYourPipe['season'] == 1415].ix[:, featureYour]
    dfYour.columns = dfYour.columns + '_op'

    # Get mean and reorder into the original feature order
    bb = pd.concat([dfTgt.mean(), dfYour.mean()])
    bb = bb.reindex(features)

    model = coef['model']
    featureCoef = pd.DataFrame({'features': features, 'coef': model.coef_[0]})
    
    return featureCoef, model.predict_proba(bb)[0][1] # The prob of tgtTeam win

def GetActions(features):
    """
    Get action recommendations for your team, given your features, 
    meaning you want INCREASE those with POSTIVE COEF, DECREASE those with NEGATIVE COEF
    """
    featureOP = []
    featureYMore = []
    featureYLess = []
    featureImprove = []
    for index, row in features[::-1].iterrows():
        if 'poss' not in row['features']:
            if '_op' in row['features']:
                if (row['coef'] > 0) and ('accuracy' not in row['features']):
                    #print 'op less ' + row['features']
                    featureOP.append(row['features'][:-3].replace('_', ' ').title())
                    featureImprove.append(row['features'])
            else:
                if row['coef'] > 0:      
                    #print 'you more ' + row['features']
                    featureYMore.append(row['features'].replace('_', ' ').title())
                    featureImprove.append(row['features'])
                else:
                    if 'accuracy' not in row['features'] and ('won' not in row['features']):
                        #print 'you less ' + row['features']
                        featureYLess.append(row['features'].replace('_', ' ').title())
                        featureImprove.append(row['features'])

    actions = pd.DataFrame([featureOP, featureYMore, featureYLess], index = ['OP', 'YMore', 'YLess']).T
    nDimActions = actions.shape
    actions = actions.values.tolist()
    for ii in np.arange(nDimActions[0]):
        for jj in np.arange(nDimActions[1]):
            if actions[ii][jj] == None:
                actions[ii][jj] = ' '
            else:
                actions[ii][jj] = actions[ii][jj].replace('Att', 'Attempt').replace('Obox', 'Out the Box').replace('Ibox', 'Inside the Box')
    return actions, featureImprove           

def ImprovedScore(tgtName, yourName, teamModels, featureImprove, teamTgtPipe, teamYourPipe, Imp = 0.1):
    """
    Given 10% improvement at the suggested features, how much more likely you are going to win
    """

    ## Put featureImprove into target model - need to reverse _op and non _op
    coef = teamModels[tgtName]
    # Get stats of Team A's win and lose matches - only 20 features are saved
    features = list(coef['features'])
    # Get stats of Team B: Revert the features of A to retrieve features for B
    featureYour = []
    featureTgt = []
    for ii in features:
        if '_op' in ii:
            featureYour.append(ii[:-3])
        else:
            featureTgt.append(ii)

    dfTgt = teamTgtPipe[teamTgtPipe['season'] == 1415].ix[:, featureTgt]
    dfYour = teamYourPipe[teamYourPipe['season'] == 1415].ix[:, featureYour]
    dfYour.columns = dfYour.columns + '_op'

    # Get mean and reorder into the original feature order
    bb = pd.concat([dfTgt.mean(), dfYour.mean()])
    bb = bb.reindex(features)
    model = coef['model']

    for ii in bb.iteritems():
        if ((ii[0] + '_op') in featureImprove) or ((ii[0][:-3]) in featureImprove):
            if model.coef_[0][features.index(ii[0])] < 0:
                bb[ii[0]] *= 1 + Imp
            else:
                bb[ii[0]] *= 1 - Imp

    probTgt = model.predict_proba(bb)[0][1]

    ## Put featureImprove into your model
    coef = teamModels[yourName]
    # Get stats of Team A's win and lose matches - only 20 features are saved
    features = list(coef['features'])
    # Get stats of Team B: Revert the features of A to retrieve features for B
    featureYour = []
    featureTgt = []
    for ii in features:
        if '_op' in ii:
            featureTgt.append(ii[:-3])
        else:
            featureYour.append(ii)

    dfTgt = teamTgtPipe[teamTgtPipe['season'] == 1415].ix[:, featureTgt]
    dfYour = teamYourPipe[teamYourPipe['season'] == 1415].ix[:, featureYour]
    dfTgt.columns = dfTgt.columns + '_op'

    # Get mean and reorder into the original feature order
    bb = pd.concat([dfTgt.mean(), dfYour.mean()])
    bb = bb.reindex(features)

    model = coef['model']
    for ii in bb.iteritems():
        if ii[0] in featureImprove:
            if model.coef_[0][features.index(ii[0])] > 0:
                bb[ii[0]] *= 1 + Imp
            else:
                bb[ii[0]] *= 1 - Imp

    probYour = model.predict_proba(bb)[0][1]

    return round(probYour / (probYour + probTgt), 2)

   
def PredictMatch(yourName, tgtName, teamModels, db):
	"""
	The main function to make prediction, recommend features, and compute improvement
	"""

	teamTgtPipe, teamYourPipe = QueryTeamData(tgtName, yourName, db)
	featureCoefTgt, probTgt = PredictOp(teamTgtPipe, teamYourPipe, tgtName, teamModels)
	featureCoefYour, probYour = PredictOp(teamYourPipe, teamTgtPipe, yourName, teamModels)
	odds = round(probYour / (probYour + probTgt), 2)

	# Only return features from your model
	# In featureCoefYour, you want INCREASE those with POSTIVE COEF, DECREASE those with NEGATIVE COEF
	# In featureCoefTgt, you want to do the opposite

	# reverse both the sign of the coef, and '_op' in features so as to be the same with featureCoefYour
	featureCoefTgt['coef'] = - featureCoefTgt['coef']
	featureCoefTgt.features = [ii[:-3] if "_op" in ii else ii + '_op' for ii in featureCoefTgt.features]
	featureBoth = featureCoefTgt[10:-1].append(featureCoefYour[10:-1])

	# get action recommendations
	featureBoth.drop_duplicates(subset = 'features', take_last = True, inplace = True)
	actions, featureImprove = GetActions(featureBoth)
	Imp = 0.1
	oddsNew = ImprovedScore(tgtName, yourName, teamModels, featureImprove, teamTgtPipe, teamYourPipe, Imp)

	return odds, oddsNew, actions
	
	
	
if __name__ == '__main__':
	teamModels = pickle.load(open('../data/teamModels.p', "rb")) # teamModels contain log models for all teams
	db = mdb.connect(user="root", host="localhost", passwd = '000000', db="teamData", charset='utf8')
	for ii in teamModels:
		for jj in teamModels:
			odds, oddsNew, actions = PredictMatch(ii, jj, teamModels, db) 
			print ii + ' ' + jj + ': ' + str(odds)
	
	
	