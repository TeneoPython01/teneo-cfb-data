# College Football Script
#
# Author(s):        BDT
# Developed:        09/02/2019
# Last Updated:     09/21/2019
# Version History:  [v01 09/02/2019] Prototype to get schedule and record info
#                   [v02 09/21/2019] Rewrite for increased efficiency
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
team_year_record_str, team_year_schedule_df = mySchedule.__FindTeamRecordByYear__('Georgia',2018)
print(team_year_record_str)
print(team_year_schedule_df)

#Print to screen: Series record information for num_past_years when Wake has played Florida State
recent_series_record_str, recent_series_schedule_df = mySchedule.__FindTeamVsOpponentRecentSeriesRecord__('Wake Forest','Florida State')
print(recent_series_record_str)
print(recent_series_schedule_df)





"""
OLD SCRIPT CODE FOLLOWS:

#import dependencies
import sys #This is used to set the sys path for importing the module
#sys.path.append('./college_football_data_class') #This is where the module resides
#from __init__ import Schedule #This is the module with classes related to cfb data
import college_football_data_class as cfb_data #This is the module with classes related to cfb data

# ignore deprecation warnings for now until able to incorporate better handling
#import warnings
#warnings.filterwarnings("ignore")

# Needed for df handling
import pandas as pd

# Needed for datetime handling
from datetime import datetime as dt

# Eventually, will want to re-enable sending alert emails
# once git ignore list and config.ini is usable
#import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.base import MIMEBase
#from email.mime.text import MIMEText
#from email.utils import COMMASPACE, formatdate
#from email import encoders


time_now = dt.now()

# Set list of teams to track
team_list = ['Wake Forest','Florida State','Northwestern']

# Initialize email body as empty string
body_str = """
"""

# Display information for each team in the team_list
for team_item in team_list:
    #Run process on Wednesday morning only
    #if ((time_now.weekday() == 2) & (time_now.hour <= 11)):
    #    print("run this process on Wed AM only")

    #Set the properties to be used
    #team1 = "Wake Forest"
    team1 = team_item
    game_yr = 2019
    num_past_years = 5
    #game_wk = 15 # optional param for get_game_wk_info(), default is 1

    now_time = dt.now()

    #initialize an object with class Schedule
    schedule = cfb_data.Schedule(team1, game_yr, num_past_years)# game_wk is optional param for get_game_wk_info(), default is 1

    # populate the properties of the object
    schedule.find_last_completed_game_info() # filter information from schedule for last completed game info
    schedule.find_next_game_info()
    schedule.find_series_range_record(schedule.nextgameinfoframe.opponent)
    schedule.summarize_opponent_record(schedule.nextgameinfoframe.opponent, schedule.seriesrangerecordsummaryframe.year)
    schedule.summarize_team_record(schedule.seriesrangerecordsummaryframe.year)
    schedule.combine_series_and_record_info()

    print('\n' + team_item + ': NEXT GAME INFO FRAME\n')
    body_str = body_str + '</br></br><b>' + '\n' + team_item + ': NEXT GAME INFO FRAME\n' +'\n' + '</b>'

    df_nextgame = pd.DataFrame(schedule.nextgameinfoframe[['opponent','start_time','venue']]).transpose()
    col_name = 'rec_last_' + str(num_past_years) + '_yrs'
    df_nextgame[col_name] = schedule.seriesrangerecordsummary
    print(df_nextgame)
    body_str = body_str + df_nextgame.to_html(index=False, index_names=False) + '\n'

    print('\n' + team_item + ': SERIES AND RECORD FRAME, LAST ' + str(num_past_years) + ' YEARS:\n')
    body_str = body_str + '</br></br><b>'  + '\n' + team_item + ': SERIES AND RECORD FRAME, LAST ' + str(num_past_years) + ' YEARS:\n' + '\n' + '</b></br></br>'
    
    df_seriesinfo = schedule.seriesandrecordframe[['year','week','venue','winner','team_rec','opp_rec']]
    print(df_seriesinfo)
    body_str = body_str + df_seriesinfo.to_html(index=False, index_names=False) + '\n' + '</br></br>'

    
print('\n\n\n --- --- --- \n\n\n')
"""