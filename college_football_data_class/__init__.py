# College Football Data Class Module
#
# Author(s):        BDT
# Developed:        09/02/2019
# Last Updated:     09/21/2019
# Version History:  [v01 09/02/2019] Prototype to get schedule and record info
#                   [v02 09/21/2019] Rewrite for increased efficiency
#
# Purpose:          This script is used to establish the class objects
#
# Special Notes:    n/a
#
# Dev Backlog:      1) Rewrite code for added efficiency
#                   2) Add comments
#                   3) Build record history for each team by year and for each team vs next opponent 
#                      series over num_past_years

# import cfb_func with custom path
import sys, os
sys.path.append(os.path.dirname(__file__))
import cfb_func as cfb_func

# import numpy to leverage np.where() for conditional df handling
import numpy as np

import pandas as pd


# protected properties, functions, and methods within the Base class
class Base(object):

    #__init__() "MAGIC METHOD" CREATES:
    #   self.current_status AS STR
    #   self.num_past_years AS INT
    #   self.team_list AS LIST
    #   self.current_year AS INT
    def __init__(self, num_past_years, team_list):
        self.current_status = 'STATUS INFOMATION LOG BEGIN'
        self.__SetStatusMessage__('Initializing class')
        self.num_past_years = num_past_years
        self.team_list = team_list

        self.__SetStatusMessage__('Finding current year based on system date')
        self.current_year = cfb_func.get_current_year()

        self.__SetStatusMessage__('Getting schedule information for last ' 
                              + str(self.num_past_years) + ' years')
        self.__GetMultiYearScheduleAllTeams__()
   
    #METHOD APPENDS self.current_status WITH NEW MESSAGE STRING
    def __SetStatusMessage__(self, msg=""):
        self.current_status = self.current_status + '; \n' + msg
    
    #METHOD DISPLAYS self.current_status WHICH IS STRING
    def __ShowStatus__(self):
        print(self.current_status)

    #METHOD CREATES self.df_multi_yr_schedule_all_teams AS PANDAS DATAFRAME
    #   AND CREATES self.team_schedule_frame_list[team_list_index] AS LIST
    #   AND CREATES self.html_next_game_info[team_list_index] AS LIST
    #   AND CREATES self.html_last_game_info[team_list_index] AS LIST
    #   WHERE team_list_index IS THE INDEX OF THE TEAM FROM self.team_list[]
    def __GetMultiYearScheduleAllTeams__(self):

        self.df_multi_yr_schedule_all_teams = pd.DataFrame()

        for year_item in range(self.current_year-self.num_past_years+1, self.current_year+1):

            self.__SetStatusMessage__('Getting schedule for year = ' + str(year_item))
            self.df_multi_yr_schedule_all_teams = self.df_multi_yr_schedule_all_teams.append(
                cfb_func.get_full_year_schedule_all_teams(year_item)
            )
        
        self.__SetStatusMessage__('Received all year schedules in year range provided')

        self.df_multi_yr_schedule_all_teams['on_team_watch_list'] = np.where(
            (self.df_multi_yr_schedule_all_teams['home_team'].isin(self.team_list)) 
            | (self.df_multi_yr_schedule_all_teams['away_team'].isin(self.team_list)),
            1,
            None
        )
        self.__SetStatusMessage__('Flagged games involving teams on the watch list')

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
    def __FindTeamRecordByYear__(self, record_team, record_year):
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

        df_record.drop(['game_count', 'win_count', 'loss_count'], axis=1, inplace=True)
        
        return win_loss_record, df_record

    #FUNCTION RETURNS WIN-LOSS RECORD AND SCHEDULE INFO FOR A GIVEN TEAM-OPPONENT
    #PAIRING OVER THE COURSE OF A SERIES THAT SPANS FROM num_past_years SEASONS
    #AGO UNTIL CURRENT SEASON
    def __FindTeamVsOpponentRecentSeriesRecord__(self, series_team, series_opponent):
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
            'season_type',#
            'series_team',#
            'series_opponent',#
            'team_pts',#
            'opponent_pts',#
            'winner',#
            'team_venue',#
            'team_win_bool'
        ]]

        
        
        
        df_series['game_count'] = df_series.groupby('series_team')['team_win_bool'].count().iloc[-1]
        df_series['win_count'] = df_series.groupby('series_team')['team_win_bool'].sum().iloc[-1]
        df_series['loss_count'] = df_series['game_count'] - df_series['win_count']
        
        win_loss_record = str(df_series['win_count'].iloc[-1]) + '-' + str(df_series['loss_count'].iloc[-1])

        df_series = df_series[[
            'season',
            'week',
            'season_type',#
            'series_team',#
            'series_opponent',#
            'team_pts',#
            'opponent_pts',#
            'winner',#
            'team_venue'#
        ]]

        
        return win_loss_record, df_series
        
        


        
        
        
        
        
    #needs rewrite:
    def __combineSeriesAndRecordInfo__(self):
        #combine:
        # self.seriesrangerecordsummary (year is key to join on)
        # self.opponentrecordframe (need to summarize to win-loss by year format)
        # self.teamrecordframe (need to summarize to win-loss by year format)

        self.seriesandrecordframe = self.seriesrangerecordsummaryframe

        df_temp1_win = self.opponentrecordframe.groupby('year')['team_win_bool'].sum().reset_index()
        df_temp1_loss = self.opponentrecordframe.groupby('year')['game_count'].mean().reset_index()
        df_temp1_rec = df_temp1_win.merge(df_temp1_loss, how='inner', on='year')

        df_temp1_rec['win_count'] = df_temp1_rec['team_win_bool']
        df_temp1_rec['loss_count'] = df_temp1_rec['game_count'] - df_temp1_rec['win_count']
        df_temp1_rec['opp_rec'] = df_temp1_rec['win_count'].astype('str') + '-' + df_temp1_rec['loss_count'].astype('str')
        df_temp1_rec = df_temp1_rec[['year','opp_rec']]

        #print(df_temp1_rec)

        df_temp2_win = self.teamrecordframe.groupby('year')['team_win_bool'].sum().reset_index()
        df_temp2_loss = self.teamrecordframe.groupby('year')['game_count'].mean().reset_index()
        df_temp2_rec = df_temp2_win.merge(df_temp2_loss, how='inner', on='year')

        df_temp2_rec['win_count'] = df_temp2_rec['team_win_bool']
        df_temp2_rec['loss_count'] = df_temp2_rec['game_count'] - df_temp2_rec['win_count']
        df_temp2_rec['team_rec'] = df_temp2_rec['win_count'].astype('str') + '-' + df_temp2_rec['loss_count'].astype('str')
        df_temp2_rec = df_temp2_rec[['year','team_rec']]

        #print(df_temp2_rec)

        df3_temp = self.seriesandrecordframe.merge(df_temp1_rec, how='inner', on='year', suffixes=('_l',''))
        df3_temp = df3_temp.merge(df_temp2_rec, how='inner', on='year', suffixes=('_l',''))

        #df3_temp.drop(['opp_rec_l', 'team_rec_l'], axis=1, inplace=True)

        #self.seriesandrecordframe = self.seriesandrecordframe.merge(df_temp1_rec, how='inner', on='year')
        #self.seriesandrecordframe = self.seriesandrecordframe.merge(df_temp2_rec, how='inner', on='year')
        self.seriesandrecordframe = df3_temp




    
# this is the class used by the user, which instanciates a Base() class for protection
class Schedule(Base):

    def __init__(self, num_past_years=0, team_list=[]):
        super(Schedule, self).__init__(num_past_years, team_list)

    def get_multi_year_schedule_all_teams(self):
        self.__GetMultiYearScheduleAllTeams__()

    def show_status(self):
        self.__ShowStatus__()
        
    def team_records_by_year(self):
        self.__TeamListRecordsByYear__()
        
        

        
        
    #needs rewrite:
    def combine_series_and_record_info(self):
        self.__combineSeriesAndRecordInfo__()