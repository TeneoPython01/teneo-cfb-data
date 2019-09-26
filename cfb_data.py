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
# Dev Backlog:      1) Rewrite code for added efficiency
#                   2) Add comments
#                   3) Incorporate better handling for deprecation and other warnings
#                   4) Research importing all dependencies via module
#                   5) Add support for config.ini to pull u/n and pass for sending email
#                      and leverage git ignore list to prevent uploading credentials
#                      to github
#                   6) Install and leverage a local database for ingestion instead of
#                      dataframes in local memory
#                   7) Write function for following: When converting df.to_html(), use
#                      string handling to incorporate <style> tags for better display
#                   8) Trigger team_records_by_year() upon __init__() but handle cases
#                      where team_list is empty to prevent index error on [0]
#                   9) Fix handling for HTML conversion of dfs to be more modularized (header, style, table, footer)


# import dependencies
import os, sys
sys.path.append('./college_football_data_class/')
import college_football_data_class as cfb_data

# define teams to watch and
# grab the last 5 years of college football schedule information
team_list = ['Wake Forest', 'Florida State', 'Northwestern']
mySchedule = cfb_data.Schedule(5, team_list)

# show the schedule frame
#print(mySchedule.df_multi_yr_schedule_all_teams)

# show the class status log
#mySchedule.show_status()


# as example, show sched info for the first item from the team list
for i in range(len(mySchedule.html_next_game_info)):
    print('NEXT GAME SCHEDULED FOR ' + mySchedule.team_schedule_frame_list[i]['my_team'].iloc[0])
    print(mySchedule.html_next_game_info[i])
    print('\n<br><br>\n')

    print('LAST GAME RESULTS FOR ' + mySchedule.team_schedule_frame_list[i]['my_team'].iloc[0])
    print(mySchedule.html_last_game_info[i])
    print('\n<br><br>\n')

#Print to screen: Team record information for UGA, 2018 season
team_year_schedule_df = mySchedule.FindTeamRecordByYear('Georgia',2018)[1]
print(mySchedule.df_to_html(team_year_schedule_df, 1))

#Print to screen: Series record information for num_past_years when Wake has played Florida State
recent_series_schedule_df = mySchedule.FindTeamVsOpponentRecentSeriesRecord('Wake Forest','Florida State')[1]
print(mySchedule.df_to_html(recent_series_schedule_df, 1))

