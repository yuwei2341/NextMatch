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

def QueryTeamData(tgtName, yourName):
	"""
	Get data from MySQL DB
	"""
	con = mdb.connect('localhost', 'root', '000000', 'data') #host, user, password, #database
	with con:
		cur = con.cursor()
		print tgtName.replace(' ', '_')
		print yourName.replace(' ', '_')
		teamTgtPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + tgtName.replace(' ', '_'), con = con)
		teamYourPipe = pd.io.sql.read_sql(sql = "SELECT * FROM " + yourName.replace(' ', '_'), con = con)
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
    
    
def PredictMatch(yourName, tgtName, teamModels):
    teamTgtPipe, teamYourPipe = QueryTeamData(tgtName, yourName)
    featureCoefTgt, probTgt = PredictOp(teamTgtPipe, teamYourPipe, tgtName, teamModels)
    featureCoefYour, probYour = PredictOp(teamYourPipe, teamTgtPipe, yourName, teamModels)
    
    # Only return features from your model
    # In featureCoefYour, you want INCREASE those with POSTIVE COEF, DECREASE those with NEGATIVE COEF
    # In featureCoefTgt, you want to do the opposite
    return round(probYour / (probYour + probTgt), 2), featureCoefYour, featureCoefTgt

	
def GetActions(features):
    """
    Get action recommendations for your team
    """
    featureOP = []
    featureYMore = []
    featureYLess = []
    for index, row in features[::-1].iterrows():
        if 'poss' not in row['features']:
            if '_op' in row['features']:
                if (row['coef'] > 0) and ('accuracy' not in row['features']):
                    print 'op less ' + row['features']
                    featureOP.append(row['features'][:-3].replace('_', ' ').title())
            else:
                if row['coef'] > 0:      
                    print 'you more ' + row['features']
                    featureYMore.append(row['features'].replace('_', ' ').title())
                else:
                    if 'accuracy' not in row['features'] and ('won' not in row['features']):
                        print 'you less ' + row['features']
                        featureYLess.append(row['features'].replace('_', ' ').title())

    actions = pd.DataFrame([featureOP, featureYMore, featureYLess], index = ['OP', 'YMore', 'YLess']).T
    nDimActions = actions.shape
    actions = actions.values.tolist()
    for ii in np.arange(nDimActions[0]):
        for jj in np.arange(nDimActions[1]):
            if actions[ii][jj] == None:
                actions[ii][jj] = ' '
            else:
                actions[ii][jj] = actions[ii][jj].replace('Att', 'Attempt').replace('Obox', 'Out the Box').replace('Ibox', 'Inside the Box')
    return actions                                         
	
if __name__ == '__main__':
	print 'I am a module'