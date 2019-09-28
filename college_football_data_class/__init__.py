# College Football Data Class Module
#
# Author(s):        BDT
# Developed:        09/02/2019
# Last Updated:     09/25/2019
# Version History:  [v01 09/02/2019] Prototype to get schedule and record info
#                   [v02 09/21/2019] Rewrite for increased efficiency
#                   [v03 09/25/2019] Rewrite completed
#
# Purpose:          This script is used to establish the class objects
#
# Special Notes:    n/a
#
# Dev Backlog:      1) Rewrite code for added efficiency
#                   2) Add comments
#                   3) Build record history for each team by year and for each team vs next opponent 
#                      series over num_past_years
#                   4) Fix handling for HTML conversion of dfs to be more modularized (header, style, table, footer)

# import cfb_func with custom path
import sys, os
sys.path.append(os.path.dirname(__file__))
import cfb_func as cfb_func

#import configparser to pull variables from config.ini file
#note that config.ini is excluded from the repo, but can be
#built by editing config_template.ini with a text editor
#and saving in the same directory as config.ini
import configparser

# import numpy to leverage np.where() for conditional df handling
import numpy as np

import pandas as pd

#initialize the config parser and read in from config.ini
config = configparser.ConfigParser()
config.read('./config/config.ini')

#pull the teams to watch from the config into a list.  the
#method used requires dropping (pop()) the first value.
config_team_list = config['SCHEDULE']['teams to watch'].split('\n')
config_team_list.pop(0)

#pull the number of past years worth of schedule data to pull
#from the config file
config_num_past_years = int(config['SCHEDULE']['num past years'])


#establish the Schedule class
class Schedule(object):

    #__init__() "MAGIC METHOD" CREATES:
    #   self.current_status AS STR
    #   self.num_past_years AS INT
    #   self.team_list AS LIST
    #   self.current_year AS INT
    def __init__(self):
        self.current_status = 'STATUS INFOMATION LOG BEGIN'
        self.__SetStatusMessage('Initializing class')

        #set the num_past_years and team_list based on data from config.ini
        self.num_past_years = config_num_past_years
        self.team_list = config_team_list

        self.__SetStatusMessage('Finding current year based on system date')
        self.current_year = cfb_func.get_current_year()

        self.__SetStatusMessage('Getting schedule information for last ' 
                              + str(self.num_past_years) + ' years')
        self.GetMultiYearScheduleAllTeams()
   
    #METHOD APPENDS self.current_status WITH NEW MESSAGE STRING
    #DUNDER PREFIX (__) MANGLES THE FUNCTION FOR PRIVATE
    #MODULE USE ONLY
    def __SetStatusMessage(self, msg=""):
        self.current_status = self.current_status + '; \n' + msg
    
    #FUNCTION RETURNS self.current_status WHICH IS STRING
    def ShowStatus(self):
        return self.current_status

    #METHOD CREATES self.df_multi_yr_schedule_all_teams AS PANDAS DATAFRAME
    #   AND CREATES self.team_schedule_frame_list[team_list_index] AS LIST
    #   AND CREATES self.html_next_game_info[team_list_index] AS LIST
    #   AND CREATES self.html_last_game_info[team_list_index] AS LIST
    #   WHERE team_list_index IS THE INDEX OF THE TEAM FROM self.team_list[]
    def GetMultiYearScheduleAllTeams(self):

        self.df_multi_yr_schedule_all_teams = pd.DataFrame()

        for year_item in range(self.current_year-self.num_past_years+1, self.current_year+1):

            self.__SetStatusMessage('Getting schedule for year = ' + str(year_item))
            self.df_multi_yr_schedule_all_teams = self.df_multi_yr_schedule_all_teams.append(
                cfb_func.get_full_year_schedule_all_teams(year_item)
            )
        
        self.__SetStatusMessage('Received all year schedules in year range provided')

        self.df_multi_yr_schedule_all_teams['on_team_watch_list'] = np.where(
            (self.df_multi_yr_schedule_all_teams['home_team'].isin(self.team_list)) 
            | (self.df_multi_yr_schedule_all_teams['away_team'].isin(self.team_list)),
            1,
            None
        )
        self.__SetStatusMessage('Flagged games involving teams on the watch list')

        #initialize the list that will hold the team schedule dfs
        self.team_schedule_frame_list = []
        
        #initialize the lists that will hold the HTML information
        self.html_next_game_info = []
        self.html_last_game_info = []
        self.html_current_season_info = []
        
        #initialize the for loop counter
        count = 0

        #iterate through the teams in the team watch list
        for team_item in self.team_list:
            #append the full all-team multi-year schedule to the list
            self.team_schedule_frame_list.append(self.df_multi_yr_schedule_all_teams.copy())
            
            #this line of code may seem redundant, but it clears the dreaded
            #"copy of a slice of a copy of a whatever" warning
            self.team_schedule_frame_list[count] = self.team_schedule_frame_list[count].copy()

            #filter the current position of the list's df to just the current team_item
            self.team_schedule_frame_list[count] = self.team_schedule_frame_list[count][
                (self.team_schedule_frame_list[count]['home_team']==team_item)
                | (self.team_schedule_frame_list[count]['away_team']==team_item)
            ]
            
            #add additional columns to the current position of the list's df
            self.team_schedule_frame_list[count]['my_team'] = team_item
            self.team_schedule_frame_list[count]['opponent'] = np.where(
                self.team_schedule_frame_list[count]['home_team'] == team_item,
                self.team_schedule_frame_list[count]['away_team'],
                self.team_schedule_frame_list[count]['home_team']
            )
            self.team_schedule_frame_list[count]['team_pts'] = None
            self.team_schedule_frame_list[count]['opponent_pts'] = None
            
            self.team_schedule_frame_list[count]['team_pts'] = np.where(
                self.team_schedule_frame_list[count]['home_team'] == team_item,
                self.team_schedule_frame_list[count]['home_points'],
                self.team_schedule_frame_list[count]['team_pts']
            )
            self.team_schedule_frame_list[count]['team_pts'] = np.where(
                self.team_schedule_frame_list[count]['away_team'] == team_item,
                self.team_schedule_frame_list[count]['away_points'],
                self.team_schedule_frame_list[count]['team_pts']
            )
            self.team_schedule_frame_list[count]['opponent_pts'] = np.where(
                self.team_schedule_frame_list[count]['home_team'] == team_item,
                self.team_schedule_frame_list[count]['away_points'],
                self.team_schedule_frame_list[count]['opponent_pts']
            )
            self.team_schedule_frame_list[count]['opponent_pts'] = np.where(
                self.team_schedule_frame_list[count]['away_team'] == team_item,
                self.team_schedule_frame_list[count]['home_points'],
                self.team_schedule_frame_list[count]['opponent_pts']
            )
            self.team_schedule_frame_list[count]['winner'] = np.where(
                self.team_schedule_frame_list[count]['home_points'] > \
                self.team_schedule_frame_list[count]['away_points'],
                self.team_schedule_frame_list[count]['home_team'],
                self.team_schedule_frame_list[count]['away_team']
            )
            self.team_schedule_frame_list[count]['team_venue'] = np.where(
                self.team_schedule_frame_list[count]['home_team'] == team_item,
                'Home',
                'Away'
            )
            self.team_schedule_frame_list[count]['team_win_bool'] = np.where(
                self.team_schedule_frame_list[count]['team_pts'] > 
                self.team_schedule_frame_list[count]['opponent_pts'],
                1,
                0
            )
            
            self.team_schedule_frame_list[count]['is_current_season_bool'] = np.where(
                (self.team_schedule_frame_list[count]['season'] == 
                     self.team_schedule_frame_list[count][
                         self.team_schedule_frame_list[count]['team_pts'] >= 0
                     ].iloc[-1]['season']
                ),
                1,
                0
            )

            self.team_schedule_frame_list[count]['is_last_game_bool'] = np.where(
                (self.team_schedule_frame_list[count]['team_pts'] >= 0) &
                (self.team_schedule_frame_list[count]['week'] == 
                     self.team_schedule_frame_list[count][
                         self.team_schedule_frame_list[count]['team_pts'] >= 0
                     ].iloc[-1]['week']
                ) &
                (self.team_schedule_frame_list[count]['season'] == 
                     self.team_schedule_frame_list[count][
                         self.team_schedule_frame_list[count]['team_pts'] >= 0
                     ].iloc[-1]['season']
                ),
                1,
                0
            )

            self.team_schedule_frame_list[count]['is_next_game_bool'] = np.where(
                (self.team_schedule_frame_list[count]['team_pts'].isnull()) &
                (self.team_schedule_frame_list[count]['week'] == 
                     self.team_schedule_frame_list[count][
                         self.team_schedule_frame_list[count]['team_pts'].isnull()
                     ].iloc[0]['week']
                ),
                1,
                0
            )

            #define the desired columns to be kept
            columns_to_keep = [
                #'id', 
                'season', 
                'week', 
                'season_type', 
                #'start_date', 
                #'neutral_site',
                #'conference_game', 
                #'attendance', 
                #'venue_id', 
                #'venue', 
                #'home_team',
                #'home_conference', 
                #'home_points', 
                #'home_line_scores', 
                #'away_team',
                #'away_conference', 
                #'away_points', 
                #'away_line_scores', 
                #'start_time_dt',
                'start_time_str', 
                #'start_year_dtper', 
                'start_year_int',
                #'on_team_watch_list', 
                'my_team', 
                'opponent',
                'team_pts', 
                'opponent_pts',
                'winner',
                'team_venue', 
                'team_win_bool',
                'is_current_season_bool',
                'is_last_game_bool',
                'is_next_game_bool'
            ]
            
            #reduce the current list position's df down to just the desired columns
            self.team_schedule_frame_list[count] = self.team_schedule_frame_list[count][columns_to_keep]
            
            
            self.html_next_game_info.append('')
            self.html_next_game_info[count] = self.html_next_game_info[count] + \
            self.team_schedule_frame_list[count][
                self.team_schedule_frame_list[count]['is_next_game_bool'] == 1][
                ['season',
                 'week',
                 'start_time_str',
                 'my_team',
                 'opponent']
                ].to_html(index=False).replace('\n','')

            
            self.html_last_game_info.append('')
            self.html_last_game_info[count] = self.html_last_game_info[count] + \
            self.team_schedule_frame_list[count][
                self.team_schedule_frame_list[count]['is_last_game_bool'] == 1][
                ['season',
                 'week',
                 'season_type',
                 'start_time_str',
                 'start_year_int',
                 'my_team',
                 'opponent',
                 'team_pts',
                 'opponent_pts',
                 'winner',
                 'team_venue']
            ].to_html(index=False).replace('\n','')

            #increment the for loop counter
            count = count + 1
        
    #FUNCTION RETURNS WIN-LOSS RECORD FOR A GIVEN TEAM AND SEASON
    #SEASON IS YEAR, MUST BE WITHIN LAST num_past_years YEARS
    def FindTeamRecordByYear(self, record_team, record_year):

        #force record_year param into int type (otherwise sometimes
        #it gets autotyped as str, which causes issues)
        record_year = int(record_year)
        
        #create a df to hold the team records
        df_record = pd.DataFrame()
        df_record = self.df_multi_yr_schedule_all_teams.copy()
        #seems redundant, but this suppresses the copy/slice/copy warning
        df_record = df_record.copy()
        
        #create new fields used to calculate record
        df_record['record_team'] = record_team
        df_record['team_pts'] = None
        df_record['opponent_pts'] = None

        df_record['team_pts'] = np.where(
            df_record['home_team'] == record_team,
            df_record['home_points'],
            df_record['team_pts']
        )
        df_record['team_pts'] = np.where(
            df_record['away_team'] == record_team,
            df_record['away_points'],
            df_record['team_pts']
        )
        df_record['opponent_pts'] = np.where(
            df_record['home_team'] == record_team,
            df_record['away_points'],
            df_record['opponent_pts']
        )
        df_record['opponent_pts'] = np.where(
            df_record['away_team'] == record_team,
            df_record['home_points'],
            df_record['opponent_pts']
        )
        df_record['team_win_bool'] = np.where(
            df_record['team_pts'] > 
            df_record['opponent_pts'],
            1,
            0
        )
        df_record['winner'] = np.where(
            df_record['home_points'] > df_record['away_points'],
            df_record['home_team'],
            df_record['away_team']
        )
        df_record['team_venue'] = np.where(
            df_record['home_team'] == record_team,
            'Home',
            'Away'
        )
            
        df_record = df_record[
            (
                (df_record['home_team'] == record_team) |
                (df_record['away_team'] == record_team)
            ) &
            (df_record['season'] == record_year) &
            (df_record['team_pts'] >= 0)
        ]
        
        #df_record = df_record[['record_team', 'season', 'week', 'team_win_bool']]

        df_record['game_count'] = df_record.groupby('season')['team_win_bool'].count().iloc[-1]
        df_record['win_count'] = df_record.groupby('season')['team_win_bool'].sum().iloc[-1]
        df_record['loss_count'] = df_record['game_count'] - df_record['win_count']
        
        win_loss_record = str(df_record['win_count'].iloc[-1]) + '-' + str(df_record['loss_count'].iloc[-1])

        #df_record.drop(['game_count', 'win_count', 'loss_count'], axis=1, inplace=True)
        df_record = df_record[[
            'season',
            'week',
            'season_type',
            #'series_team',
            #'series_opponent',
            'team_pts',
            'opponent_pts',
            'winner',
            'team_venue'
        ]]
        
        return win_loss_record, df_record

    #FUNCTION RETURNS WIN-LOSS RECORD AND SCHEDULE INFO FOR A GIVEN TEAM-OPPONENT
    #PAIRING OVER THE COURSE OF A SERIES THAT SPANS FROM num_past_years SEASONS
    #AGO UNTIL CURRENT SEASON
    def FindTeamVsOpponentRecentSeriesRecord(self, series_team, series_opponent):
        #create a df to hold the series records
        df_series = pd.DataFrame()
        df_series = self.df_multi_yr_schedule_all_teams.copy()
        #seems redundant, but this suppresses the copy/slice/copy warning
        df_series = df_series.copy()
        
        #create new fields used to calculate record
        df_series['series_team'] = series_team
        df_series['series_opponent'] = series_opponent
        df_series['team_pts'] = None
        df_series['opponent_pts'] = None

        df_series['team_pts'] = np.where(
            df_series['home_team'] == series_team,
            df_series['home_points'],
            df_series['team_pts']
        )
        df_series['team_pts'] = np.where(
            df_series['away_team'] == series_team,
            df_series['away_points'],
            df_series['team_pts']
        )
        df_series['opponent_pts'] = np.where(
            df_series['home_team'] == series_team,
            df_series['away_points'],
            df_series['opponent_pts']
        )
        df_series['opponent_pts'] = np.where(
            df_series['away_team'] == series_team,
            df_series['home_points'],
            df_series['opponent_pts']
        )
        df_series['team_win_bool'] = np.where(
            df_series['team_pts'] > 
            df_series['opponent_pts'],
            1,
            0
        )
        df_series['winner'] = np.where(
            df_series['home_points'] > df_series['away_points'],
            df_series['home_team'],
            df_series['away_team']
        )
        df_series['team_venue'] = np.where(
            df_series['home_team'] == series_team,
            'Home',
            'Away'
        )
            
        df_series = df_series[
            (
                (df_series['home_team'] == series_team) |
                (df_series['away_team'] == series_team)
            ) &
            (
                (df_series['home_team'] == series_opponent) |
                (df_series['away_team'] == series_opponent)
            ) &
            (
                df_series['home_team'] != df_series['away_team']
            ) &
            (
                df_series['team_pts'] >= 0
            )
        ]
        
        df_series = df_series[[
            'season',
            'week',
            'season_type',
            'series_team',
            'series_opponent',
            'team_pts',
            'opponent_pts',
            'winner',
            'team_venue',
            'team_win_bool'
        ]]

        
        
        
        df_series['game_count'] = df_series.groupby('series_team')['team_win_bool'].count().iloc[-1]
        df_series['win_count'] = df_series.groupby('series_team')['team_win_bool'].sum().iloc[-1]
        df_series['loss_count'] = df_series['game_count'] - df_series['win_count']
        
        win_loss_record = str(df_series['win_count'].iloc[-1]) + '-' + str(df_series['loss_count'].iloc[-1])

        df_series = df_series[[
            'season',
            'week',
            'season_type',
            #'series_team',
            #'series_opponent',
            'team_pts',
            'opponent_pts',
            'winner',
            'team_venue'
        ]]
        
        df_series['team_yr_rec'] = ''
        df_series['opp_yr_rec'] = ''
        new_df_series = pd.DataFrame()
        
        for index, row in df_series.iterrows():
            row['team_yr_rec'] = str(self.FindTeamRecordByYear(series_team, row['season'])[0])
            row['opp_yr_rec'] = str(self.FindTeamRecordByYear(series_opponent, row['season'])[0])
            new_df_series = new_df_series.append(row)

        new_df_series = new_df_series[
            [
                'season',
                'week',
                'season_type',
                'team_pts',
                'opponent_pts',
                'winner',
                'team_venue',
                'team_yr_rec',
                'opp_yr_rec'
            ]
        ]

        new_df_series['season'] = pd.to_numeric(new_df_series['season'], downcast='integer')
        new_df_series['week'] = pd.to_numeric(new_df_series['week'], downcast='integer')
        new_df_series['team_pts'] = pd.to_numeric(new_df_series['team_pts'], downcast='integer')
        new_df_series['opponent_pts'] = pd.to_numeric(new_df_series['opponent_pts'], downcast='integer')
        
        return win_loss_record, new_df_series

    def df_to_html(self, my_title, df_or_df_list, df_description_or_list):
        
        if type(df_or_df_list) is not list:
            df_or_df_list = [ df_or_df_list ]

        if type(df_description_or_list) is not list:
            df_description_or_list = [ df_description_or_list ]
           
        loop_count = 0
        
        html_script = ''
        html_script = html_script + cfb_func.html_header(my_title)
        html_script = html_script + cfb_func.html_style_header()

        for df_item in df_or_df_list:
            html_script = html_script + '<H3><B><U>' + df_description_or_list[loop_count] + ':</B></U></H3><BR>\n'
            html_script = html_script + cfb_func.html_from_df(df_item)
            html_script = html_script + '\n\n<BR><BR>\n\n'
            loop_count = loop_count + 1
        
        html_script = html_script + cfb_func.html_footer()

        return html_script