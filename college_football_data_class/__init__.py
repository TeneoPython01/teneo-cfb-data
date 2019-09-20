import sys, os
sys.path.append(os.path.dirname(__file__))

import cfb_data_v01 as cfb_data

import numpy as np

class Base(object):

  def __init__(self, team1, game_yr, num_past_years, game_wk):
    self.team1 = team1
    self.game_yr = game_yr
    self.num_past_years = num_past_years
    self.game_wk = game_wk

  def __request_gameframe__(self):
    gameframe = cfb_data.get_gameframe(self.team1, self.game_yr, self.num_past_years, self.game_wk)
    return gameframe

  def __getGameframe__(self):
    self.gameframe = self.__request_gameframe__()

  def __getGameWkInfo__(self):
    #add properties for:
    self.weekframe = self.gameframe[(self.gameframe['week']==self.game_wk) & (self.gameframe['year']==self.game_yr)].iloc[-1]

    self.start_time = self.weekframe['start_time']
    self.opponent = self.weekframe['opponent']
    self.team_side = self.weekframe['team_side']
    self.team_pts = self.weekframe['team_pts']
    self.opponent_pts = self.weekframe['opponent_pts']
    self.winner = self.weekframe['winner']
    self.team_win = self.weekframe['team_win']
    self.win_by = self.weekframe['win_by']
    self.pts_diff = self.weekframe['pts_diff']

  def __findLastCompletedGameInfo__(self):
    self.lastcompletedgameinfoframe = self.gameframe[~self.gameframe['pts_diff'].isna()].iloc[-1]
    self.lcg_team = self.team1
    self.lcg_opponent = self.lastcompletedgameinfoframe['opponent']
    self.lcg_winner = self.lastcompletedgameinfoframe['winner']
    self.lcg_team_pts = self.lastcompletedgameinfoframe['team_pts']
    self.lcg_opponent_pts = self.lastcompletedgameinfoframe['opponent_pts']
    self.lcg_win_by = self.lastcompletedgameinfoframe['win_by']
    self.lcg_week = self.lastcompletedgameinfoframe['week']

  def __findNextGameInfo__(self):
    self.lastcompletedgameinfoframe = self.gameframe[~self.gameframe['pts_diff'].isna()].iloc[-1]
    self.lcg_week = self.lastcompletedgameinfoframe['week']
    self.nextgameinfoframe = self.gameframe[(self.gameframe['year']==self.game_yr) & (self.gameframe['week']==self.lcg_week+1)].iloc[-1]

  def __findSeriesRangeRecordSummary__(self):
    self.seriesrangerecordsummaryframe=self.seriesrangerecordframe[['year','week','venue','team_pts','opponent_pts','winner','team_win','win_by']]
    self.seriesrangerecordsummaryframe['team_win_bool'] = np.where(self.seriesrangerecordsummaryframe['team_win']=='X',1,0)
    self.seriesrangerecordsummary_wins = self.seriesrangerecordsummaryframe['team_win_bool'].sum()
    self.seriesrangerecordsummary_total = self.seriesrangerecordsummaryframe['team_win_bool'].count()
    self.seriesrangerecordsummary_losses = self.seriesrangerecordsummary_total - self.seriesrangerecordsummary_wins
    self.seriesrangerecordsummary = str(self.seriesrangerecordsummary_wins) + '-' + str(self.seriesrangerecordsummary_losses)

    self.seriesrangerecordsummaryframe.drop(['team_win_bool'], axis=1, inplace=True)
    

  def __findSeriesRangeRecord__(self, opponent):
    self.seriesrangerecordframe = self.gameframe[(self.gameframe['opponent']==opponent) & (self.gameframe['team_pts'] >= 0)]
    self.__findSeriesRangeRecordSummary__()

  def __summarizeOpponentRecord__(self, opponent, year_list):
    self.opponentrecordframe = cfb_data.get_opponent_record_frame(opponent, year_list)

  def __summarizeTeamRecord__(self, year_list):
    self.teamrecordframe = cfb_data.get_team_record_frame(self.team1, year_list)

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

class Schedule(Base):

  def __init__(self, team1, game_yr, num_past_years, game_wk=1):
    super(Schedule, self).__init__(team1, game_yr, num_past_years, game_wk)
    self.team1 = team1
    self.game_yr = game_yr
    self.game_wk = game_wk
    super(Schedule, self).__getGameframe__()

  def get_gameframe(self):
    self.__getGameframe__()

  def get_game_wk_info(self):
    self.__getGameWkInfo__()

  def find_last_completed_game_info(self):
    self.__findLastCompletedGameInfo__()

  def find_next_game_info(self):
    self.__findNextGameInfo__()

  def find_series_range_record(self, opponent):
    #self.__findNextGameInfo__()
    self.__findSeriesRangeRecord__(opponent)

  def summarize_opponent_record(self, opponent, year_list):
    self.__summarizeOpponentRecord__(opponent, year_list)

  def summarize_team_record(self, year_list):
    self.__summarizeTeamRecord__(year_list)

  def combine_series_and_record_info(self):
    self.__combineSeriesAndRecordInfo__()
