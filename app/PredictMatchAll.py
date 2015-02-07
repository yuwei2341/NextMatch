# module for comparing stats and making recommendataions
"""
Read team names from user input, retrieve features of teams from MySQL DB, compute odds of winning and recommend features to care
"""

import numpy as np
import pandas as pd
import pymysql as mdb
from sklearn import linear_model 

def QueryTeamData(tgtName, yourName, db):
	"""
	Get data from MySQL DB
	"""
	#cur = db.cursor()
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
    featureYAcc = []
    featureImprove = []
    count = 0
    for index, row in features[::-1].iterrows():
    	if count > 8: # Don't recommend more than 9 actions
    		break
        if 'poss' not in row['features']:
            if '_op' in row['features']:
                if (row['coef'] > 0) and ('accuracy' not in row['features']):
                    featureOP.append(row['features'][:-3].replace('_', ' ').title())
                    featureImprove.append(row['features'])
                    count += 1
            else:
                if row['coef'] > 0:
                    if 'accuracy' not in row['features']:
                        featureYMore.append(row['features'].replace('_', ' ').title())
                        featureImprove.append(row['features'])
                        count += 1
                    else:
                        featureYAcc.append(row['features'].replace('_', ' ').title())
                        featureImprove.append(row['features'])
                        count += 1

    # Whether show 2 columns or 3
    useTwoCol = True
    if useTwoCol:
        actions = pd.DataFrame([featureYAcc + featureYMore, featureOP], index = ['Your', 'OP']).T

    else:
        actions = pd.DataFrame([featureYAcc, featureYMore, featureOP], index = ['YAcc', 'YMore', 'OP']).T
    nDimActions = actions.shape
    actions = actions.values.tolist()
	
    ## Make the actions more readable
    for ii in np.arange(nDimActions[0]):
        for jj in np.arange(nDimActions[1]):
            #print actions[ii][jj]
            if actions[ii][jj] == None:
                actions[ii][jj] = ' '
            else:
                actions[ii][jj] = actions[ii][jj].replace('Att', 'Attempt').replace('Obox', 'Outside the Penalty Box').replace('Ibox', 'Inside the Penalty Box').replace('Total ', '').replace('Fwd', 'Forward').replace('18Yardplus', 'Outside the Penalty Box').replace('18Yard', 'Inside the Penalty Box')
                if 'Accuracy' in actions[ii][jj]:
                    actions[ii][jj] = actions[ii][jj][9:] + ' Accuracy'
                else:
                    actions[ii][jj] = '# of ' + actions[ii][jj]
                    if ("alls" not in actions[ii][jj]) and ("Penalty Box" not in actions[ii][jj]):
                        if "Won" in actions[ii][jj]:
                            actions[ii][jj] = actions[ii][jj][:-4] + 's Won'
                        elif actions[ii][jj][-2:] != 'ss':
                            actions[ii][jj] = actions[ii][jj] + 's'
                        else:
                            actions[ii][jj] = actions[ii][jj] + 'es'
    #print actions
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

    # In featureCoefYour, you want INCREASE those with POSTIVE COEF, DECREASE those with NEGATIVE COEF
    # In featureCoefTgt, you want to do the opposite

    # reverse both the sign of the coef, and '_op' in features so as to be the same with featureCoefYour
    featureCoefTgt['coef'] = - featureCoefTgt['coef']
    featureCoefTgt.features = [ii[:-3] if "_op" in ii else ii + '_op' for ii in featureCoefTgt.features]

    # Combine only the most important 10 features
    featureBoth = featureCoefTgt[11:].append(featureCoefYour[11:])

    # get action recommendations
    # Somehow the pandas here uses a deprecated para cols, instaed of the new one subset
    #featureBoth.drop_duplicates(subset = 'features', take_last = True, inplace = True)
    featureBoth.drop_duplicates(cols = 'features', take_last = True, inplace = True)
    actions, featureImprove = GetActions(featureBoth)
    Imp = 0.1
    oddsNew = ImprovedScore(tgtName, yourName, teamModels, featureImprove, teamTgtPipe, teamYourPipe, Imp)

    return odds, oddsNew, actions
	
	
	
if __name__ == '__main__':
	print 'I\'m a module'
	
	
	
