
# College Football Functions
#
# Author(s):        BDT
# Developed:        09/02/2019
# Last Updated:     09/21/2019
# Version History:  [v01 09/02/2019] Prototype to get schedule and record info
#                   [v02 09/21/2019] Rewrite for increased efficiency
#
# Purpose:          This script is used by the college_football_data_class
#                   module for various functions
#
# Special Notes:    n/a
#
# Dev Backlog:      1) Rewrite code for added efficiency
#                   2) Add comments

import pandas as pd #to handle data in pandas dataframes
pd.set_option('display.max_rows', 500) #allow printing lots of rows to screen
pd.set_option('display.max_columns', 500) #allow printsin lots of cols to screen
pd.set_option('display.width', 1000) #don't wrap lots of columns

import requests #to pull JSON data
import numpy as np #to do conditional pandas operations
import datetime as dt #to track datetime stamps

from dateutil import tz #for timezone handling with datetime dtypes
api_mask = '%Y-%m-%dT%H:%M:%S.000Z' #this is the datetime string
                                    #format native to the API
                                    #output
readable_mask = "%a %m/%d/%Y %I:%M%p %Z" #this is a readable format
year_mask = "%Y" #just the year
from_zone = tz.tzutc() #API datetimes are in UTC time
to_zone = tz.tzlocal() #Used for converting to local timezone


def get_full_year_schedule_all_teams(year):
    r = requests.get('https://api.collegefootballdata.com/games?year=' + str(year)).json()

    df = pd.DataFrame(r)
    
    df['start_time_dt'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone)
    df['start_time_str'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone).strftime(readable_mask)
    df['start_year_dtper'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone).tz_convert(None).to_period('Y')
    df['start_year_int'] = df['start_year_dtper'].astype(int) + 1970
    
    return df


def get_current_year():
    return int(dt.datetime.now().year)


# Original prototype function; deprecated; will be rewritten
# Returns the opponent of a particular game
def get_opponent(team1, game_yr, game_wk):

  r = requests.get('https://api.collegefootballdata.com/games?year=' +
                   str(game_yr) + '&week=' +
                   str(game_wk) + '&team=' +
                   team1).json()

  df = pd.DataFrame(r)

  df['opponent'] = np.where(team1==df['home_team'],df['away_team'],df['home_team'])

  opponent = df.iloc[-1, df.columns.get_loc('opponent')]

  return opponent



# Original prototype function; deprecated; will be rewritten
# Returns the full schedule for a given team and year range
# note that week is not used
def get_gameframe(team1, game_yr, num_past_years, game_wk):

  df = pd.DataFrame()

  for item_yr in range(game_yr-num_past_years, game_yr+1):
    for wk in range(1,20):
      r = requests.get('https://api.collegefootballdata.com/games?year=' +
                       str(item_yr) + '&week=' +
                       str(wk) + '&team=' +
                       team1).json()

      df = df.append(pd.DataFrame(r))

      if 'start_time' not in df:
          df['start_time'] = dt.datetime.strptime(df['start_date'].iloc[-1],api_mask).replace(tzinfo=from_zone).astimezone(to_zone).strftime(readable_mask)
      else:
          df.iloc[-1, df.columns.get_loc('start_time')] = dt.datetime.strptime(df['start_date'].iloc[-1],api_mask).replace(tzinfo=from_zone).astimezone(to_zone).strftime(readable_mask)

      if 'year' not in df:
          df['year'] = int(dt.datetime.strptime(df['start_date'].iloc[-1],api_mask).replace(tzinfo=from_zone).astimezone(to_zone).strftime(year_mask))
      else:
          df.iloc[-1, df.columns.get_loc('year')] = int(dt.datetime.strptime(df['start_date'].iloc[-1],api_mask).replace(tzinfo=from_zone).astimezone(to_zone).strftime(year_mask))

  df['year'] = pd.to_numeric(df['year'], downcast='integer')
  df['opponent'] = np.where(team1==df['home_team'],df['away_team'],df['home_team'])
  df['team_side'] = np.where(team1==df['home_team'],'home','away')
  df['team_pts'] = np.where(team1==df['home_team'],df['home_points'],df['away_points'])
  df['opponent_pts'] = np.where(team1==df['home_team'],df['away_points'],df['home_points'])
  df['winner'] = np.where(df['team_pts']>df['opponent_pts'],team1,df['opponent'])
  df['team_win'] = np.where(df['team_pts']>df['opponent_pts'],'X','')
  df['win_by'] = np.where(df['team_pts']>df['opponent_pts'],df['team_pts']-df['opponent_pts'],df['opponent_pts']-df['team_pts'])
  df['pts_diff'] = df['team_pts'] - df['opponent_pts']


  return df





# Original prototype function; deprecated; will be rewritten
# Returns a df with a team's win/loss record for a given year
def get_opponent_record_frame(opponent, year_list):
  df = pd.DataFrame()

  for item_year in year_list:
    df = df.append(get_gameframe(opponent, item_year, 0, 0))

  df_summary = df[['year','team_win']]
  df_summary['team_win_bool'] = np.where(df_summary['team_win']=='X',1,0)
  df_summary = df_summary[['year','team_win_bool']]
  df_summary['game_count'] = df_summary.groupby('year')['team_win_bool'].count().iloc[-1]
  df_summary['win_count'] = df_summary.groupby('year')['team_win_bool'].sum().iloc[-1]
  df_summary['loss_count'] = df_summary['game_count'] - df_summary['win_count']
                   
  return df_summary






# Original prototype function; deprecated; will be rewritten
# Returns a df with a team's win/loss record for a given year
def get_team_record_frame(team1, year_list):
  df = pd.DataFrame()

  for item_year in year_list:
    df = df.append(get_gameframe(team1, item_year, 0, 0))

  df_summary = df[['year','team_win']]
  df_summary['team_win_bool'] = np.where(df_summary['team_win']=='X',1,0)
  df_summary = df_summary[['year','team_win_bool']]
  df_summary['game_count'] = df_summary.groupby('year')['team_win_bool'].count().iloc[-1]
  df_summary['win_count'] = df_summary.groupby('year')['team_win_bool'].sum().iloc[-1]
  df_summary['loss_count'] = df_summary['game_count'] - df_summary['win_count']
                   
  return df_summary
