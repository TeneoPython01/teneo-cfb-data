# College Football Data Class Module
#
# Author(s):        TeneoPython01@gmail.com
# Developed:        09/02/2019
# Last Updated:     10/11/2019
#
# Purpose:          This script is used to establish the schedule class and 
#                   its attributes
#
# Special Notes:    n/a

#import cfb_func with custom path
import sys, os
sys.path.append(os.path.dirname(__file__))
import cfb_func as cfb_func

#import configparser to pull variables from config.ini file
#note that config.ini is excluded from the repo, but can be
#built by editing config_template.ini with a text editor
#and saving in the same directory as config.ini
import configparser
config = configparser.ConfigParser()
config.read('./config/config.ini')

#import numpy to leverage np.where() for
#conditional df handling
import numpy as np

#import pandas for dataframes
import pandas as pd

#set formatted string used for displaying the
#rank for unranked teams
ur_str = '(unranked)'

#establish the Schedule class
class Schedule(object):

    #__init__() "MAGIC METHOD" sets the current season
    #and then runs a couple methods to set up class
    #properties using the config file and cfb APIs
    def __init__(self):
        #set current year
        self.current_year = cfb_func.get_current_year()

        #pull watchlist teams and other config data
        self.__start_configparser()
        
        #pull all schedule and rank data
        self.GetMultiYearScheduleAllTeams()


    #PULL CONFIG DATA LIKE WATCHLIST TEAMS
    def __start_configparser(self):

        #pull the teams to watch from the config into a list.  the
        #method used requires dropping (pop()) the first value.
        config_team_list = config['SCHEDULE']['teams to watch'].split('\n')
        config_team_list.pop(0)

        #if the config file isnt properly configured with at
        #least one team, then kill the program
        if len(config_team_list) == 0:
            print('NO WATCHLIST TEAMS FOUND IN CONFIG.INI.')
            exit()

        #identify the number of past years worth of schedule data to pull
        #from the config file
        config_num_past_years = int(config['SCHEDULE']['num past years'])

        #set the num_past_years and team_list based on data from config.ini
        self.num_past_years = config_num_past_years
        self.team_list = config_team_list



    #PULL ALL SCHEDULE AND RANK DATA
    #Store the information as follows:
    # 1) self.df_multi_yr_schedule_all_teams
    #       holds the schedule for all years in range for 
    #       every team
    # 2) self.team_schedule_frame_list[team_list_index]
    #       contains the schedule for all years for the teams
    #       on the watch list
    # 3) self.next_game_list[team_list_index] 
    #       contains information for the next upcoming game
    #       for each team on the watch list
    # 4) self.last_game_list[team_list_index] 
    #       contains information for the most recently 
    #       completed game for each team on the watch list
    # 5) self.prior_matchup_next_opp_list[team_list_index]
    #       contains information for all historical matchups 
    #       where a team on the watchlist played their next 
    #       opponent in next_game_list
    # 6) self.all_ranking_data
    #       contains all season and all week rank data for
    #       the years in range
    def GetMultiYearScheduleAllTeams(self):

        #set up a coupleof  empty dataframes
        self.df_multi_yr_schedule_all_teams = pd.DataFrame()
        self.all_ranking_data = pd.DataFrame()
        self.all_poll_data = pd.DataFrame()
        
        #for all years in range
        for year_item in range(self.current_year-self.num_past_years+1,
                               self.current_year+1):

            #populate self.df_multi_yr_schedule_all_teams with the
            #schedule data for each year in range
            self.df_multi_yr_schedule_all_teams = \
            self.df_multi_yr_schedule_all_teams.append(
                cfb_func.get_full_year_schedule_all_teams(year_item)
            )
            #populate self.all_ranking_data with the AP ranking data
            #for every week for each year in range
            self.all_ranking_data = self.all_ranking_data.append(
                cfb_func.get_rankings_all_weeks(year_item)
            )
            self.all_poll_data = self.all_poll_data.append(
                cfb_func.get_poll_data(year_item)
            )

        #merge the ranking data into self.df_multi_yr_schedule_all_teams
        self.df_multi_yr_schedule_all_teams = \
        self.__merge_rankings_into_schedule_data(
            self.df_multi_yr_schedule_all_teams,
            self.all_ranking_data[[
                'season',
                'week',
                'team',
                'rank',
                'prev_rank',
                'rank_chg'
            ]]
        )
        
        #filter self.all_ranking_data down to just the latest
        #season & week ranking data
        self.current_ranking_data = self.all_ranking_data[
            (self.all_ranking_data['season_week'] == \
             self.all_ranking_data['season_week'].max()
            )
        ]

        #flag records in the schedule frame for teams on the watch list
        self.df_multi_yr_schedule_all_teams['on_team_watch_list'] = np.where(
            (self.df_multi_yr_schedule_all_teams['home_team'].isin(self.team_list))
            | (self.df_multi_yr_schedule_all_teams['away_team'].isin(self.team_list)),
            1,
            None
        )

        #initialize the lists that will hold the dfs for watchlist teams.
        #these will be lists of frames.
        self.team_schedule_frame_list = []
        self.next_game_list = []
        self.last_game_list = []
        self.all_prior_matchup_next_opp_list = []
        
        #initialize the for loop counter
        count = 0

        #iterate through the teams in the team watch list
        for team_item in self.team_list:

            #append the full all-team multi-year schedule to 
            #the team_schedule_frame_list df
            self.team_schedule_frame_list.append(
                self.df_multi_yr_schedule_all_teams.copy()
            )

            #clear "copy of a slice" warning
            self.team_schedule_frame_list[count] = \
            self.team_schedule_frame_list[count].copy() 

            #filter the current position of the list's
            #df to just the current team_item
            self.team_schedule_frame_list[count] = \
            self.team_schedule_frame_list[count][
                (self.team_schedule_frame_list[count]['home_team']==team_item)
                | (self.team_schedule_frame_list[count]['away_team']==team_item)
            ]
            
            #add additional columns to the current position of the list's df
            self.__add_new_fields_to_team_schedule_frame_list(count, team_item)
            
            #define the desired columns to be kept
            columns_to_keep = [
                'season', 
                'week', 
                'season_type', 
                'start_time_str', 
                'my_team', 
                'opponent',
                'team_pts', 
                'opponent_pts',
                'winner',
                'team_venue', 
                'team_win_bool',
                'is_current_season_bool',
                'is_last_game_bool',
                'is_next_game_bool',
                'team_rank',
                'team_prev_rank',
                'team_rank_chg',
                'opponent_rank',
                'opponent_prev_rank',
                'opponent_rank_chg'
            ]
            
            #reduce the current list position's df down to
            #just the desired columns
            self.team_schedule_frame_list[count] = \
            self.team_schedule_frame_list[count][columns_to_keep]
            
            #build the next_game_list frame
            self.__build_next_game_list_frame(count)
            
            #build the last_game_list frame
            self.__build_last_game_list_frame(count)
            
            #build the all_prior_matchup_next_opp_list frame
            self.__build_all_prior_matchup_next_opp_list_frame(count)
            
            #increment the for loop counter
            count = count + 1

        
    #FUNCTION RETURNS WIN-LOSS RECORD AND SCHEDULE FOR 
    #A GIVEN TEAM AND SEASON.
    #Example Uses:
    #       team_record_string = self.FindTeamRecordByYear('Georgia',2017)[0]
    #       team_record_details_dataframe = self.FindTeamRecordByYear('Georgia',2017)[1]
    def FindTeamRecordByYear(self, record_team, record_year):

        #force record_year param into int type
        record_year = int(record_year)
        
        #create a df to hold the team records
        df_record = pd.DataFrame()
        df_record = self.df_multi_yr_schedule_all_teams.copy()
        df_record = df_record.copy() #suppress the copy/slice/copy warning
        
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
        df_record['my_team'] = record_team
        df_record['series_opponent'] = np.where(
            df_record['home_team'] == record_team,
            df_record['away_team'],
            df_record['home_team']
        )
        df_record['opponent'] = np.where(
            df_record['away_team'] == record_team,
            df_record['home_team'],
            df_record['away_team']
        )
        
        df_record = df_record[
            (
                (df_record['home_team'] == record_team) |
                (df_record['away_team'] == record_team)
            ) &
            (df_record['season'] == record_year) &
            (df_record['team_pts'] >= 0)
        ]
        
        df_record['game_count'] = df_record.groupby('season')['team_win_bool'].count().iloc[-1]
        df_record['win_count'] = df_record.groupby('season')['team_win_bool'].sum().iloc[-1]
        df_record['loss_count'] = df_record['game_count'] - df_record['win_count']
        
        win_loss_record = str(df_record['win_count'].iloc[-1]) + '-' + \
        str(df_record['loss_count'].iloc[-1])


        df_record['team_rank'] = np.where(
            df_record['away_team'] == record_team,
            df_record['away_team_rank'],
            df_record['home_team_rank']
        )
        df_record['opponent_rank'] = np.where(
            df_record['away_team'] == record_team,
            df_record['home_team_rank'],
            df_record['away_team_rank']
        )

        df_record = df_record[[
            'season',
            'week',
            'season_type',
            'my_team',
            'team_rank',
            'opponent',
            'opponent_rank',
            'team_pts',
            'opponent_pts',
            'winner',
            'team_venue'
        ]]

        #CONVERT RANKING TO STRING SO UNRANKED CAN BE BLANKED OUT
        #RANK 26 REPRESENTS UNRANKED
        df_record = self.__format_rank_26(df_record, 'team_rank', ur_str, 1)
        df_record = self.__format_rank_26(df_record, 'opponent_rank', ur_str, 1)
        
        return win_loss_record, df_record

    #FUNCTION RETURNS WIN-LOSS RECORD AND SCHEDULE INFO FOR A GIVEN TEAM-OPPONENT
    #PAIRING OVER THE COURSE OF A SERIES THAT SPANS FROM num_past_years SEASONS
    #AGO UNTIL CURRENT SEASON
    # Example Uses:
    #       series_win_loss_record_string = FindTeamVsOpponentRecentSeriesRecord('Nebraska', 'Northwestern')[0]
    #       series_win_loss_details_dataframe = FindTeamVsOpponentRecentSeriesRecord('Nebraska', 'Northwestern')[1]
    def FindTeamVsOpponentRecentSeriesRecord(self, series_team, series_opponent):

        #create empty df to hold the series records
        df_series = pd.DataFrame()
        df_series = self.df_multi_yr_schedule_all_teams.copy()
        df_series = df_series.copy() #suppress the copy/slice/copy warning
        
        
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
            
        #print(1,df_series[df_series['home_team']==series_team])
        #print(2,df_series[df_series['away_team']==series_team])

        #print(3,df_series[df_series['home_team']==series_opponent])
        #print(4,df_series[df_series['away_team']==series_opponent])
        
        #print(5,df_series[df_series['home_team'] != df_series['away_team']])
        
        #print(6,df_series[df_series['team_pts'] >= 0])

        
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
        
        #print(777,df_series)

        columns_to_keep = [
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
        ]

        df_series = df_series[columns_to_keep]
        
        if len(df_series.index) == 0:
            df_series['game_count'] = 0
            df_series['win_count'] = 0
            df_series['loss_count'] = 0
            win_loss_record = '0-0'
        else:
            df_series['game_count'] = df_series.groupby('series_team')['team_win_bool'].count().iloc[-1]
            df_series['win_count'] = df_series.groupby('series_team')['team_win_bool'].sum().iloc[-1]
            df_series['loss_count'] = df_series['game_count'] - df_series['win_count']

            win_loss_record = str(df_series['win_count'].iloc[-1]) + '-' + \
            str(df_series['loss_count'].iloc[-1])

        columns_to_keep = [
            'season',
            'week',
            'season_type',
            'team_pts',
            'opponent_pts',
            'winner',
            'team_venue'
        ]

        df_series = df_series[columns_to_keep]
        
        df_series['team_yr_rec'] = ''
        df_series['opp_yr_rec'] = ''
        new_df_series = pd.DataFrame()
        
        for index, row in df_series.iterrows():
            row['team_yr_rec'] = str(self.FindTeamRecordByYear(series_team, row['season'])[0])
            row['opp_yr_rec'] = str(self.FindTeamRecordByYear(series_opponent, row['season'])[0])
            new_df_series = new_df_series.append(row)

        columns_to_keep = [
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

        #print(len(df_series.index))
        #print(df_series)
        #print(len(new_df_series.index))
        #print(new_df_series)
        
        if len(df_series.index) == 0:
            pass
        else:
            new_df_series = new_df_series[columns_to_keep]
            new_df_series['season'] = pd.to_numeric(new_df_series['season'], downcast='integer')
            new_df_series['week'] = pd.to_numeric(new_df_series['week'], downcast='integer')
            new_df_series['team_pts'] = pd.to_numeric(new_df_series['team_pts'], downcast='integer')
            new_df_series['opponent_pts'] = pd.to_numeric(new_df_series['opponent_pts'], downcast='integer')
        
        return win_loss_record, new_df_series

    #CONVERTS DATAFRAME (OR LIST OF DFs) INTO A SINGLE HTML STRING
    #TO BETTER DISPLAY TABLES
    #    my_title: Title of the HTML page
    #    df_or_df_list: The dataframe (or multiple dataframes in a list)
    #    df_description_or_list: a string or list of strings that 
    #        describe each corresponding dataframe
    # Example Uses:
    #        my_html_string = df_to_html(
    #            'A Page Of Tables',
    #            [homes_a_df, homes_b_df, homes_c_df],
    #            ['Homes in neighborhood A', 'Homes in neighborhood B', 'Homes in neighborhood C']
    #        )
    def df_to_html(self, my_title, df_or_df_list, df_description_or_list):
        
        #if param calls a string, convert to list
        if type(df_or_df_list) is not list:
            df_or_df_list = [ df_or_df_list ]

        #if param calls a string, convert to list
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
    
    #METHOD EMAILS THE SCHEDULE DATA AS HTML ATTACHMENT
    #EMAIL SERVER CONNECTION IS DEFINED IN CONFIG.INI
    # Example Uses:
    #        self.send_scheudle_html('This is the subject', 'Dear so and so, How are you?', attachment_filename)
    def send_schedule_html(self, subject='[Teneo] - CFB Schedule Info', message='Needs body', files=[]):
        send_from = config['OUTGOING EMAIL']['from']
        #send_to = config['OUTGOING EMAIL']['to']
        send_to = config['OUTGOING EMAIL']['to'].split('\n')
        send_to.pop(0)
        server = config['OUTGOING EMAIL']['server']
        port = config['OUTGOING EMAIL']['port']
        username = config['OUTGOING EMAIL']['username']
        password = config['OUTGOING EMAIL']['password']
        use_tls = config['OUTGOING EMAIL']['use_tls']

        path = config['PATH']['html']
        filename = 'schedule'
        filename_timestamp = cfb_func.get_current_datetime_int()[2]
        filename_extension = '.html'
        fullpath = path + filename + filename_timestamp + filename_extension

        with open(fullpath, "w") as text_file:
            print(message, file=text_file)

        files.append(fullpath)
        
        cfb_func.sendmail(send_from, send_to, subject, message, files,
              server, port, username, password,
              use_tls)

    #FUNTION FINDS THE RANK FOR A GIVEN SEASON, WEEK, TEAM
    #COMBINATION.  IF THE GIVEN PARAMETERS DON'T RETURN
    #RANKING INFORMATION, IMPUTE THAT THE DATA IN QUESTION
    #REFERENCES A TEAM THAT WAS UNRANKED AT THE GIVEN
    #TIME.  RANK 26 REFERS TO UNRANKED.
    #
    #NOTE: PREV_RANK SHOULD ACTUALLY LOOK TO PRIOR WEEK
    #INFO TO DETERMINE PRIOR RANK, AND THEN RANK_CHG
    #SHOULD BE CALCULATED.  THIS IS NOT CURRENTLY CODED
    #SO THIS WILL REQUIRE ENHANCEMENT IN THE FUTURE.
    #
    #USAGE:
    #   rank_df, rank_str = RankForTeamLineItem(2019, 7, 'Wake Forest')
    def RankForTeamAtPointInTime(self, season, week, team):
        #create empty df as a pandas dataframe
        df = pd.DataFrame()

        #make df a copy of the ranking data for the given season/week/team
        #parameters passed to the function
        df = self.all_ranking_data[
            (self.all_ranking_data['season'] == season)
            & (self.all_ranking_data['week'] == week)
            & (self.all_ranking_data['team'] == team)
        ][['season','week','team','rank','prev_rank','rank_chg']].copy()
        
        #if df is empty, that means that the given parameters
        #are for a team that wasn't ranked at the given point in time.
        #in that case, populate df with proxy data representing that
        #the team was unranked at that time.  rank #26 is a value
        #used in this code base to represent unranked, since the
        #ranking data source only shows the top 25 teams.  therefore,
        #the code considers all unranked teams to be tied for rank #26.
        if df.empty:
            temp_data = {
                'season': season, 
                'week': week,
                'team': team,
                'rank': 26,
                'prev_rank': 26,
                'rank_chg': 0
            }
            df = pd.DataFrame(data=temp_data, index=[0])
        
        df = self.__format_rank_26(df, 'rank', ur_str, 0)
        
        #return df (the dataframe) as well as the rank
        #in the form of a string.  see usage to understand
        #how to parse these values when calling the
        #function
        return df, df['rank'].astype(str)

    #FUNCTION MERGES THE SEASON-BY-SEASON WEEK-BY-WEEK AP RANKING
    #DATA INTO THE MULTIYR ALL TEAM SCHEDULE DATA
    #USAGE:
    #   df = __merge_rankings_into_schedule_data(multiyr_schedule_df, rankings_df):
    def __merge_rankings_into_schedule_data(self, schedule_df, rankings_df):

        #temp_df1 is the schedule data
        temp_rank_df1 = schedule_df.copy()

        #temp_df2 is the ranking data
        temp_rank_df2 = rankings_df.copy()

        #temp_df3 is where temp_dfs 1 and 2 get combined
        #start with merging on home_team
        temp_rank_df3 = temp_rank_df1.merge(
            temp_rank_df2,
            how='left',
            left_on=['season','week','home_team'],
            right_on=['season','week','team'],
            suffixes=('_l','_r')
        )

        #set all unranked teams to rank 26 and prev
        #rank 26 so rank_chg can be calced
        temp_rank_df3[['rank','prev_rank']] = \
        temp_rank_df3[['rank','prev_rank']].fillna(26)

        #calc rank_chg
        temp_rank_df3['rank_chg'] = \
        temp_rank_df3['prev_rank'] - temp_rank_df3['rank']

        #rename columns
        temp_rank_df3.rename(
            columns={
                'team':'home_team_drop',
                'rank':'home_team_rank',
                'prev_rank':'home_team_prev_rank',
                'rank_chg':'home_team_rank_chg'
            },
            inplace=True
        )

        #set all unranked teams to rank 26 and prev
        #rank 26 so rank_chg can be calced
        temp_rank_df3[[
            'home_team_rank',
            'home_team_prev_rank',
            'home_team_rank_chg'
        ]] = temp_rank_df3[[
            'home_team_rank',
            'home_team_prev_rank',
            'home_team_rank_chg'
        ]].fillna(26).astype(int).round()

        #temp_df3 is where temp_dfs 1 and 2 get combined
        #now merge on away_team
        temp_rank_df3 = temp_rank_df3.merge(
            temp_rank_df2,
            how='left',
            left_on=['season','week','away_team'],
            right_on=['season','week','team'],
            suffixes=('_l','_r')
        )

        #set all unranked teams to rank 26 and prev
        #rank 26 so rank_chg can be calced
        temp_rank_df3[[
            'rank',
            'prev_rank'
        ]] = temp_rank_df3[[
            'rank',
            'prev_rank'
        ]].fillna(26)

        #calc rank_chg
        temp_rank_df3['rank_chg'] = (
            temp_rank_df3['prev_rank'] - temp_rank_df3['rank']
        )

        #rename columns
        temp_rank_df3.rename(
            columns={
                'team':'away_team_drop',
                'rank':'away_team_rank',
                'prev_rank':'away_team_prev_rank',
                'rank_chg':'away_team_rank_chg'
            },
            inplace=True
        )

        #set all unranked teams to rank 26 and prev
        #rank 26 so rank_chg can be calced
        temp_rank_df3[[
            'away_team_rank',
            'away_team_prev_rank',
            'away_team_rank_chg'
        ]] = temp_rank_df3[[
            'away_team_rank',
            'away_team_prev_rank',
            'away_team_rank_chg'
        ]].fillna(26).astype(int).round()
        
        #drop unneeded columns
        temp_rank_df3.drop(
            [
                'home_team_drop',
                'away_team_drop'
            ], axis=1, inplace=True
        )
        
        return temp_rank_df3

    def __add_new_fields_to_team_schedule_frame_list(self, count, team_item):

        #add additional columns to the current position of the list's df
        self.team_schedule_frame_list[count]['my_team'] = team_item
        self.team_schedule_frame_list[count]['team_pts'] = None
        self.team_schedule_frame_list[count]['opponent_pts'] = None

        self.team_schedule_frame_list[count]['opponent'] = np.where(
            self.team_schedule_frame_list[count]['home_team'] == team_item,
            self.team_schedule_frame_list[count]['away_team'],
            self.team_schedule_frame_list[count]['home_team']
        )

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

        self.team_schedule_frame_list[count]['team_rank'] = np.where(
            self.team_schedule_frame_list[count]['away_team'] == team_item,
            self.team_schedule_frame_list[count]['away_team_rank'],
            self.team_schedule_frame_list[count]['home_team_rank']
        )

        self.team_schedule_frame_list[count]['team_prev_rank'] = np.where(
            self.team_schedule_frame_list[count]['away_team'] == team_item,
            self.team_schedule_frame_list[count]['away_team_prev_rank'],
            self.team_schedule_frame_list[count]['home_team_prev_rank']
        )

        self.team_schedule_frame_list[count]['team_rank_chg'] = np.where(
            self.team_schedule_frame_list[count]['away_team'] == team_item,
            self.team_schedule_frame_list[count]['away_team_rank_chg'],
            self.team_schedule_frame_list[count]['home_team_rank_chg']
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

        self.team_schedule_frame_list[count]['opponent_rank'] = np.where(
            self.team_schedule_frame_list[count]['away_team'] == team_item,
            self.team_schedule_frame_list[count]['home_team_rank'],
            self.team_schedule_frame_list[count]['away_team_rank']
        )

        self.team_schedule_frame_list[count]['opponent_prev_rank'] = np.where(
            self.team_schedule_frame_list[count]['away_team'] == team_item,
            self.team_schedule_frame_list[count]['home_team_prev_rank'],
            self.team_schedule_frame_list[count]['away_team_prev_rank']
        )

        self.team_schedule_frame_list[count]['opponent_rank_chg'] = np.where(
            self.team_schedule_frame_list[count]['away_team'] == team_item,
            self.team_schedule_frame_list[count]['home_team_rank_chg'],
            self.team_schedule_frame_list[count]['away_team_rank_chg']
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

        self.team_schedule_frame_list[count]['is_current_season_bool'] = \
        np.where(
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

    def __build_next_game_list_frame(self, count):
        #build the next_game_list frame
        columns_to_drop = [
            'team_pts',
            'opponent_pts',
            'winner',
            'team_win_bool',
            'is_current_season_bool',
            'is_last_game_bool',
            'is_next_game_bool'
        ]
        self.next_game_list.append(pd.DataFrame())
        self.next_game_list[count] = self.team_schedule_frame_list[count][
            (self.team_schedule_frame_list[count]['is_next_game_bool']==1)
        ].copy().drop(
            columns_to_drop,
            axis=1,
            inplace=False
        )
        self.next_game_list[count]['series_record'] = \
        self.FindTeamVsOpponentRecentSeriesRecord(
            self.next_game_list[count]['my_team'].iloc[-1], 
            self.next_game_list[count]['opponent'].iloc[-1]
        )[0]

        new_column_order = [
            'season',
            'week',
            'season_type',
            'start_time_str',
            'my_team',
            'team_rank',
            'opponent',
            'opponent_rank',
            'team_venue',
            'series_record'
        ]
        self.next_game_list[count] = \
        self.next_game_list[count][new_column_order].copy()        

        
    def __build_last_game_list_frame(self, count):
        columns_to_drop = [
            'team_win_bool',
            'is_current_season_bool',
            'is_last_game_bool',
            'is_next_game_bool'
        ]
        self.last_game_list.append(pd.DataFrame())
        self.last_game_list[count] = self.team_schedule_frame_list[count][
            (self.team_schedule_frame_list[count]['is_last_game_bool']==1)
        ].copy().drop(
            columns_to_drop,
            axis=1,
            inplace=False
        )
        self.last_game_list[count]['series_record'] = self.FindTeamVsOpponentRecentSeriesRecord(
            self.last_game_list[count]['my_team'].iloc[-1], 
            self.last_game_list[count]['opponent'].iloc[-1]
        )[0]

        self.next_game_list[count] = self.__format_rank_26(self.next_game_list[count], 'team_rank', ur_str, 0)
        self.next_game_list[count] = self.__format_rank_26(self.next_game_list[count], 'opponent_rank', ur_str, 0)
        self.last_game_list[count] = self.__format_rank_26(self.last_game_list[count], 'team_rank', ur_str, 0)
        self.last_game_list[count] = self.__format_rank_26(self.last_game_list[count], 'opponent_rank', ur_str, 0)

        new_column_order = [
            'season',
            'week',
            'season_type',
            'start_time_str',
            'my_team',
            'team_rank',
            'opponent',
            'opponent_rank',
            'team_venue',
            'series_record'
        ]
        self.last_game_list[count] = self.last_game_list[count][new_column_order].copy()
        

    def __build_all_prior_matchup_next_opp_list_frame(self, count):
        columns_to_drop = [
            'team_win_bool',
            'is_current_season_bool',
            'is_last_game_bool',
            'is_next_game_bool'
        ]
        self.all_prior_matchup_next_opp_list.append(pd.DataFrame())
        self.all_prior_matchup_next_opp_list[count] = \
        self.team_schedule_frame_list[count][
            (self.team_schedule_frame_list[count]['team_pts'] >= 0) &
            (
                (
                    (self.team_schedule_frame_list[count]['my_team']==self.next_game_list[count]['my_team'].iloc[-1]) &
                    (self.team_schedule_frame_list[count]['opponent']==self.next_game_list[count]['opponent'].iloc[-1]) 
                ) |
                (
                    (self.team_schedule_frame_list[count]['opponent']==self.next_game_list[count]['my_team'].iloc[-1]) &
                    (self.team_schedule_frame_list[count]['my_team']==self.next_game_list[count]['opponent'].iloc[-1]) 
                )
            )
        ].copy()

        new_column_order = [
            'season',
            'week',
            'season_type',
            'start_time_str',
            'my_team',
            'team_rank',
            'opponent',
            'opponent_rank',
            'team_pts',
            'opponent_pts',
            'winner',
            'team_venue'
        ]

        self.all_prior_matchup_next_opp_list[count] = self.all_prior_matchup_next_opp_list[count][new_column_order]

        #CONVERT RANKING TO STRING SO UNRANKED CAN BE BLANKED OUT
        #RANK 26 REPRESENTS UNRANKED
        self.all_prior_matchup_next_opp_list[count] = self.__format_rank_26(
            self.all_prior_matchup_next_opp_list[count], 'team_rank', ur_str, 1
        )
        self.all_prior_matchup_next_opp_list[count] = self.__format_rank_26(
            self.all_prior_matchup_next_opp_list[count], 'opponent_rank', ur_str, 1
        )

    def __format_rank_26(self, df, field, unranked_format_str=ur_str, is_multi_record_frame=1):
        
        temp_df = pd.DataFrame()
        
        temp_df = df.copy()
        temp_df = temp_df.copy()
        
        if is_multi_record_frame == 1:
            df[field] = df[field].apply(lambda x: str(x))
        elif is_multi_record_frame == 0:
            df[field] = df[field].to_string(index=False).strip()
        
        temp_df[field] = np.where(
            temp_df[field].astype(str) == '26',
            unranked_format_str,
            temp_df[field].apply(lambda x: '#' + str(x))
        )
        
        return temp_df
