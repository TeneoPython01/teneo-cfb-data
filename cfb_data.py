# College Football Script
#
# Author(s):        BDT
# Developed:        09/02/2019
# Last Updated:     09/21/2019
# Version History:  [v01 09/02/2019] Prototype to get schedule and record info
#                   [v02 09/21/2019] Rewrite for increased efficiency
#                   [v03 09/25/2019] Rewrite completed
#
# Purpose:          This script is used to display schedule and record information
#
# Special Notes:    Requires college_football_data_class module
#
# Dev Backlog:      
#                   X--Rewrite code for added efficiency
#                   2) Add comments
#                   X--Incorporate better handling for deprecation and other warnings
#                   4) Research importing all dependencies via module
#                   5) Add support for config.ini to pull u/n and pass for sending email
#                      and leverage git ignore list to prevent uploading credentials
#                      to github
#                   6) Install and leverage a local database for ingestion instead of
#                      dataframes in local memory
#                   X--Write function for following: When converting df.to_html(), use
#                      string handling to incorporate <style> tags for better display
#                   X--Trigger team_records_by_year() upon __init__()
#                   9) handle cases where team_list is empty to prevent index error on [0]
#                   X--Fix handling for HTML conversion of dfs to be more modularized (header, style, table, footer)
#                   10) add historical record for n-years to Next Upcoming Game frame that is sent in email for
#                       watchlist teams; remove bool cols from same frame; null out Winner for games that
#                       haven't happened yet, remove winner, pts, etc from same frame; show opponent in
#                       completed games list frame in email, possibly add historical record to same frame; 
#                       possibly add historical record to the most recently completed game frame in email.
#                   11) create method to replace the for() stmts that generate the df_list and
#                       description list


# import dependencies
import os, sys
sys.path.append('./college_football_data_class/')
import college_football_data_class as cfb_data

# grab the schedule information defined in config.ini
mySchedule = cfb_data.Schedule()

# show the schedule frame
#print(mySchedule.df_multi_yr_schedule_all_teams)

# show the class status log
#mySchedule.show_status()


# display schedule information for the watchlist
df_list = []
description_list = []

#PULL SCHEDULE INFORMATION FOR UPCOMING WATCHLIST GAMES
for i in range(0,len(mySchedule.team_schedule_frame_list)):
    df_list.append(
        mySchedule.team_schedule_frame_list[i][
            (mySchedule.team_schedule_frame_list[i]['is_next_game_bool']==1)
        ].copy()
    )
    description_list.append(
        'Next upcoming game scheduled for ' + str(df_list[-1]['my_team'].iloc[0])
    )

#PULL RESULTS INFORMATION FOR MOST RECENTLY COMPLETED WATCHLIST GAMES
for i in range(0,len(mySchedule.team_schedule_frame_list)):
    df_list.append(
        mySchedule.team_schedule_frame_list[i][
            (mySchedule.team_schedule_frame_list[i]['is_last_game_bool']==1)
        ].copy()
    )
    description_list.append(
        'Most recently completed game results for ' + str(df_list[-1]['my_team'].iloc[0])
    )

#PULL RESULTS INFORMATION FOR ALL COMPLETED IN-SEASON WATCHLIST GAMES
for i in range(0,len(mySchedule.team_list)):
    df_list.append(
        mySchedule.FindTeamRecordByYear(mySchedule.team_list[i],2019)[1].copy()
    )
    description_list.append(
        '2019 completed games list for ' + mySchedule.team_list[i]
    )

#send the schedule data via email
my_message = mySchedule.df_to_html(
    '[Teneo] Watchlist Schedule Data', 
    df_list, 
    description_list
)

with open("schedule.htm", "w") as text_file:
    print(my_message, file=text_file)

file_list =  ['./schedule.htm']

mySchedule.send_schedule_html('[Teneo] Watchlist Schedule Data', my_message, file_list)