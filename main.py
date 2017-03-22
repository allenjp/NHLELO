# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 18:51:12 2017

@author: Jeff
"""

import pandas as pd
import matplotlib.pyplot as plt

import matplotlib
matplotlib.style.use('ggplot')

# import data
df_2016Reg = pd.read_csv('Datasets/2016RegSeasonResults.csv')
df_2017Reg = pd.read_csv('Datasets/2017SeasonResults.csv')
df_teams = pd.read_csv('Datasets/Teams.csv')

# define a function to convert team name to id
def team_name_to_id (name):
    n_int = df_teams[df_teams['Name'] == name].Id.values[0]
    return n_int

# Convert home and visitor team names to ids
def format_season_data(season_df):
    season_df['home_id'] = season_df.Home.apply(team_name_to_id)
    season_df['visitor_id'] = season_df.Visitor.apply(team_name_to_id)
    season_df.drop(labels=['Home'], inplace=True, axis=1)
    season_df.drop(labels=['Visitor'], inplace=True, axis=1)

# create an elo dictionary - each entry will be a team
# we will track their elo change over time
elo_dict = {}

for ii, row in df_teams.iterrows():
    team_id = row.Id
    elo_dict[team_id] = []

# Standardize ELOs at 1500
df_teams['ELO'] = 1500

# Function for calculating ELO change -
# Params: Home team ID, Visiting team ID, Home team win
# Formula obtained from https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/
def calc_elo_change(HId, VId, HScore):
    # First grab current ELO
    HElo = df_teams[df_teams['Id'] == HId].ELO.values[0]
    VElo = df_teams[df_teams['Id'] == VId].ELO.values[0]

    # Transform ELOs:
    HElo_t = pow(10.0, (float(HElo / 400)))
    VElo_t = pow(10.0, (float(VElo / 400)))
    
    # Expected score for each team:
    HExp = HElo_t / (HElo_t + VElo_t)
    VExp = VElo_t / (HElo_t + VElo_t)
    
    # Set the visiting team score based on home team score:
    VScore = 1 - HScore
    
    # Finally get the final results
    # We will use k = 40
    HElo_new = HElo + 40 * (HScore - HExp)
    VElo_new = VElo + 40 * (VScore - VExp)
    
    return [HElo_new, VElo_new]

    # TODO:
        # 1. Incorporate goal differentials / OT / SO factors into ELO (DONE)
        # 2. Visualize how ELO changes over the course of a season
            # - Can be done using a df - each team is a series (DONE)
        # 3. Visualize overall standing vs ELO (Spread column)
            # - For large discrepancies, visualize average ELO of opponents
        # 4. Incorporate prior seasons' data
            # - Retain 25% of prior season ELO
            # - Visualize a team's ELO over the course of many seasons
        # 5. Consider home ice advantage
            # - Look into some stats about this
        # 6. Examine playoff ELO separately
            # - Some teams may not do well in the playoffs - why?
    
# Loop through each game in the schedule and adjust ELO of each team accordingly
def update_elo(season_df):
    for ii, row in season_df.iterrows():
        home_id = row.home_id
        visitor_id = row.visitor_id
        
        # if it's a shootout - call it a tie for ELO purposes
        if (row.OT_SO == "SO"):
            home_score = 0.5
        else:
            goal_diff = row.VG - row.HG
            
            if (goal_diff >= 3):
                home_score = 0
            elif (goal_diff == 2):
                home_score = 0.15
            
            # Factor in if the game went to OT
            elif (goal_diff == 1):
                if (row.OT_SO != "OT"):
                    home_score = 0.3
                else:
                    home_score = 0.4
            elif (goal_diff == -1):
                if (row.OT_SO != "OT"):
                    home_score = 0.7
                else:
                    home_score = 0.6
            elif (goal_diff == -2):
                home_score = 0.85
            else:
                home_score = 1
                
            
        home_elo_new, visit_elo_new = calc_elo_change(home_id, visitor_id, home_score)
        
        # Update df with new elo values
        h_index = df_teams['Id'] == home_id
        df_teams.loc[h_index, 'ELO'] = home_elo_new
    
        v_index = df_teams['Id'] == visitor_id
        df_teams.loc[v_index, 'ELO'] = visit_elo_new
    
        # update team elo dictionary (used for visualization over time)
        elo_dict[home_id].append(home_elo_new)
        elo_dict[visitor_id].append(visit_elo_new)
    
format_season_data(df_2016Reg)
format_season_data(df_2017Reg)

update_elo(df_2017Reg)

# add Spread column to see how much ELO differs from standing
df_teams['ELORank'] = df_teams['ELO'].rank(ascending=False)
df_teams['Spread'] = df_teams['ELORank'] - df_teams['OverallStand']

# print(df_teams.reindex(df_teams.Spread.abs().order().index))

# convert elo_dict to dataframe
df_2017elo = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in elo_dict.iteritems() ]))

df_2017devils = df_2017elo.iloc[:,24]

print(df_teams)

# plot elo over time of Devils
plt.figure()
df_2017devils.plot()

# plot bar graph of spread
plt.figure()
df_teams['Spread'].plot(kind='bar');

# plot histogram of elo
plt.figure()
df_teams['ELO'].hist()

# based on above spread bar graph we see -
# teams with lower elo than expected - 29,18
# teams with higher elo than expected - 14,20

# we can examine the average elo of these teams' opps
# overall goal differential may prove useful

plt.show()