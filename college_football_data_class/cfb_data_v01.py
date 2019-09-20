"""
Python module for getting stock data
original author: neberej (https://github.com/neberej)
code modified by BDT on 09/06/2019
"""

import pandas as pd #to handle data in pandas dataframes
pd.set_option('display.max_rows', 500) #allow printing lots of rows to screen
pd.set_option('display.max_columns', 500) #allow printsin lots of cols to screen
pd.set_option('display.width', 1000) #don't wrap lots of columns

import requests #to pull JSON data
import numpy as np #to do conditional pandas operations
import datetime as dt #to track datetime stamps

from dateutil import tz
api_mask = '%Y-%m-%dT%H:%M:%S.000Z'
readable_mask = "%a %m/%d/%Y %I:%M%p %Z"
year_mask = "%Y"
from_zone = tz.tzutc()
to_zone = tz.tzlocal()


def get_opponent(team1, game_yr, game_wk):

  r = requests.get('https://api.collegefootballdata.com/games?year=' +
                   str(game_yr) + '&week=' +
                   str(game_wk) + '&team=' +
                   team1).json()

  df = pd.DataFrame(r)

  df['opponent'] = np.where(team1==df['home_team'],df['away_team'],df['home_team'])

  opponent = df.iloc[-1, df.columns.get_loc('opponent')]

  return opponent

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
