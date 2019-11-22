# College Football Script
#
# Author(s):        TeneoPython01@gmail.com
# Developed:        09/02/2019
# Last Updated:     10/11/2019
#
# Purpose:          This script is used to run the program
#
# Special Notes:    Requires college_football_data_class module

# import dependencies
import os, sys
sys.path.append('./college_football_data_class/')
import college_football_data_class as cfb_data


# grab the schedule information defined in config.ini
mySchedule = cfb_data.Schedule()

# display schedule information for the watchlist
df_list = []
description_list = []

#PULL SCHEDULE INFORMATION FOR UPCOMING WATCHLIST GAMES
for i in range(0,len(mySchedule.team_schedule_frame_list)):
    df_list.append(
        mySchedule.next_game_list[i]
    )
    description_list.append(
        'Next upcoming game scheduled for ' +
        str(mySchedule.next_game_list[i]['my_team'].iloc[0])
    )

#PULL RESULTS INFORMATION FOR MOST RECENTLY COMPLETED WATCHLIST GAMES
for i in range(0,len(mySchedule.team_schedule_frame_list)):
    df_list.append(
        mySchedule.last_game_list[i]
    )
    description_list.append(
        'Most recently completed game results for ' +
        str(mySchedule.last_game_list[i]['my_team'].iloc[0])
    )

#PULL RESULTS INFORMATION FOR PRIOR MATCHUPS BETWEEN EACH WATCHLIST TEAM AND THEIR NEXT OPPONENT
for i in range(0,len(mySchedule.team_schedule_frame_list)):
    df_list.append(
        mySchedule.all_prior_matchup_next_opp_list[i]
    )
    description_list.append(
        'Recent series results for matchups between ' + 
        str(mySchedule.next_game_list[i]['my_team'].iloc[0]) +
        ' and ' +
        str(mySchedule.next_game_list[i]['opponent'].iloc[0])
    )
    
#PULL RESULTS INFORMATION FOR ALL COMPLETED IN-SEASON WATCHLIST GAMES
for i in range(0,len(mySchedule.team_list)):
    df_list.append(
        mySchedule.FindTeamRecordByYear(mySchedule.team_list[i],2019)[1]
    )
    description_list.append(
        '2019 completed games list for ' + mySchedule.team_list[i]
    )

#PULL RESULTS INFORMATION FOR ALL COMPLETED IN-SEASON WATCHLIST NEXT OPPONENT GAMES
for i in range(0,len(mySchedule.team_list)):
    df_list.append(
        mySchedule.FindTeamRecordByYear(mySchedule.next_game_list[i]['opponent'].iloc[-1],2019)[1]
    )
    description_list.append(
        '2019 completed games list for ' + mySchedule.next_game_list[i]['opponent'].iloc[-1]
    )

#send the schedule data via email
my_message = mySchedule.df_to_html(
    '[Teneo] Watchlist Schedule Data', 
    df_list, 
    description_list
)

mySchedule.send_schedule_html(
    '[Teneo] Watchlist Schedule Data', my_message
)