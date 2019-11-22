#requires the following python packages:
#   sqlalchemy
#   to install: "sudo pip install sqlalchemy" in CLI
#
#   mysql-connector
#   to install: "sudo pip install mysql-connector" in CLI
#
#also requires a MySQL or MariaDB database with
#connection parameters defined in a dbconfig.ini file

import pandas as pd
pd.set_option('display.max_rows', 1000) #allow printing lots of rows to screen
pd.set_option('display.max_columns', 1000) #allow printsin lots of cols to screen
pd.set_option('display.width', 1000) #don't wrap lots of columns

import numpy as np
import sqlalchemy
import requests #to pull JSON data
import configparser
import datetime as dt #to track datetime stamps
from dateutil import tz #for timezone handling with datetime dtypes

global_now = dt.datetime.now()
global_now_year = int(global_now.year)

#this is the datetime mask native to the API output
api_mask = '%Y-%m-%dT%H:%M:%S.000Z' 
#this is the datetime mask for readable format
readable_mask = "%a %m/%d/%Y %I:%M%p %Z" #this is a readable format
year_mask = "%Y" #just the year
from_zone = tz.tzutc() #API datetimes are in UTC time
to_zone = tz.tzlocal() #Used for converting to local timezone


config = configparser.ConfigParser()
config.read('./config/dbconfig.ini')

config2 = configparser.ConfigParser()
config2.read('./config/config.ini')

def make_list(var):
    if type(var) is not list:
        var = [ var ]

    return(var)

def rename_col(df, old_field_name, new_field_name):
    df = df.rename(
        columns = {
            old_field_name: new_field_name
        }
    )
    
    return df

def drop_col(df, fields_to_drop):
    fields_to_drop = make_list(fields_to_drop)
    
    df = df.drop(
        labels=fields_to_drop,
        axis=1
    )
    
    return df

def reorder_cols(df, new_order_list):
    old_cols_list = df.columns.tolist()
    
    old_order_list = list(range(len(old_cols_list)))
    new_order_list = make_list(new_order_list)
    
    num_old_cols = len(old_cols_list)
    num_new_cols = len(new_order_list)
    
    new_cols_list = []

    count = 0
    for old_item in old_cols_list:
        new_cols_list.append(old_cols_list[new_order_list[count]])
        count = count + 1
    
    df = df[new_cols_list]
    
    return df

class Database(object):
    
    def __init__(self):
        self.__connect('CONNECTION')
        self.num_past_years  = int(config2['SCHEDULE']['num past years'])
        self.year_list = list(range(global_now_year-self.num_past_years, global_now_year+1))
        self.team_watch_list = config2['SCHEDULE']['teams to watch'].split('\n')
        self.team_watch_list.pop(0)
    
    def __connect(self, config_header):
        # set connection parameters based on /config/dbconfig.ini
        prefix = config[config_header]['prefix']
        un = config[config_header]['un']
        pw = config[config_header]['pw']
        ip = config[config_header]['ip']
        db = config[config_header]['db']

        #create the connection object    
        con = sqlalchemy.create_engine(
            '{0}{1}:{2}@{3}/{4}'.format(prefix, un, pw, ip, db)
        )

        #clear the connection parameters for security
        un = ''
        pw = ''
        ip = ''
        db = ''

        #establish the connection
        self.connection = con

    def ingest(self, df, table_name, write_type):
        #ensure only acceptable write types are used,
        #and fall back on append in case a bad type
        #is passed.
        if write_type == 'replace':
            pass
        else:
            write_type = 'append'

        #write the df to the db table
        df.to_sql(con=self.connection, name=table_name, if_exists=write_type)
        
    def query(self, sqlstr):
        #run the query against the db
        df = pd.read_sql(sqlstr, con=self.connection)
        
        #drop the first field, which is the db table's
        #index field that is pulled from the sql
        df = df[df.columns[1:]]

        #return the result
        return df
    
    def drop_table(self, table_list):
        table_list = make_list(table_list)
        
        for table_item in table_list:
            self.connection.execute('DROP TABLE ' + table_item + ';')

    def ingest_schedule(self, year_list):

        #if year was passed as int, convert to list of ints
        year_list = make_list(self.year_list)#make_list(year_list)

        #initialize df
        df = pd.DataFrame()
        
        #pull full schedule for every year
        for year_item in year_list:
            
            #pull json data from API
            r = requests.get(
                'https://api.collegefootballdata.com/games?year=' + str(year_item) + \
                '&seasonType=both'
            ).json()

            #convert api output from json to dataframe
            #and append to df
            df = df.append(pd.DataFrame(r))

        #sort the data so that the postseason week 1 data
        # is after the regular season final week data
        df = df.sort_values(by=['season','season_type','week'], ascending=[True,False,True])

        df['season_week'] = df['season']*100 + df['week']
        df['season_week'] = df['season_week'].astype(int).round()
        
        #convert datetimes to readable format
        df['start_time_dt'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone)
        df['start_time_str'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone).strftime(readable_mask)
        
        df['home_line_scores'] = df['home_line_scores'].apply(lambda x: str(x))
        df['away_line_scores'] = df['away_line_scores'].apply(lambda x: str(x))

        df = df.merge(self.teams, how='left', left_on='home_team', right_on='team')
        df = drop_col(df, 'team')
        df = rename_col(df, 'team_id', 'home_team_id')

        df = df.merge(self.teams, how='left', left_on='away_team', right_on='team')
        df = drop_col(df, 'team')
        df = rename_col(df, 'team_id', 'away_team_id')
        
        df = rename_col(df, 'id', 'game_id')

        df = reorder_cols(df, [0,1,2,18,3,4,19,20,5,6,7,8,9,10,21,11,12,13,14,22,15,16,17])
        
        df = self.add_dtstamp_to_df(df)

        #self.ingest(df[df['season'] != current_season_year], 'cfb_schedule_hist_temp', 'replace')
        #self.ingest(df[df['season'] == current_season_year], 'cfb_schedule_current_temp', 'replace')
        self.schedules = df
        self.ingest(df, 'cfb_schedule', 'replace')

    def ingest_teams(self):

        #pull json data from API
        r = requests.get(
            'https://api.collegefootballdata.com/teams'
        ).json()
        
        df = pd.DataFrame(r)
        
        df['logos'] = df['logos'].apply(
            lambda x: str(x).replace(
                "['","").replace(
                "']"," ").replace(
                "', '",", "
            )
        )
        
        df = rename_col(df, 'school', 'team')
        df = rename_col(df, 'id', 'team_id')
        
        df = self.add_dtstamp_to_df(df)

        self.ingest(df, 'cfb_teams', 'replace')
        self.teams = df[['team','team_id']]
        

    def ingest_venues(self):

        #pull json data from API
        r = requests.get(
            'https://api.collegefootballdata.com/venues'
        ).json()
        
        df = pd.DataFrame(r)
        
        #convert location field from dict containing
        #x and y coordinates into two columns, one
        #containing the x value and the other for y
        df = pd.concat([df.drop(['location'], axis=1), df['location'].apply(pd.Series)], axis=1)
        
        df = self.add_dtstamp_to_df(df)

        self.ingest(df, 'cfb_venues', 'replace')

    def ingest_talent(self, year_list):

        #if year was passed as int, convert to list of ints
        year_list = make_list(self.year_list)

        #initialize df
        df = pd.DataFrame()
        
        #pull full schedule for every year
        for year_item in year_list:

            #pull json data from API
            r = requests.get(
                    'https://api.collegefootballdata.com/talent?year=' + str(year_item) + \
                    '&seasonType=both'
            ).json()

            df = df.append(pd.DataFrame(r))
        
        df = rename_col(df, 'school', 'team')
        df = df.merge(self.teams, how='left', on='team')
        df = reorder_cols(df, [0,3,1,2])
        df['talent'] = df['talent'].astype(float).round(2)
        
        df = self.add_dtstamp_to_df(df)

        #self.ingest(df[df['year'] != current_season_year], 'cfb_talent_hist_temp', 'replace')
        #self.ingest(df[df['year'] == current_season_year], 'cfb_talent_current_temp', 'replace')
        
        self.ingest(df, 'cfb_talent', 'replace')

    def ingest_player_usage(self, year_list):

        year_list = make_list(year_list)
        
        df_excl = pd.DataFrame()
        df_incl = pd.DataFrame()
        df_all  = pd.DataFrame()

        #for every year
        for year_item in year_list:

            #pull json data from API
            r_excl = requests.get(
                    'https://api.collegefootballdata.com/player/usage?year=' + str(year_item) + \
                    '&excludeGarbageTime=true'
            ).json()

            r_incl = requests.get(
                    'https://api.collegefootballdata.com/player/usage?year=' + str(year_item) + \
                    '&excludeGarbageTime=false'
            ).json()

            df_excl = df_excl.append(pd.DataFrame(r_excl))
            df_incl = df_incl.append(pd.DataFrame(r_incl))

        df_excl = pd.concat([df_excl.drop(['usage'], axis=1), df_excl['usage'].apply(pd.Series)], axis=1)
        df_incl = pd.concat([df_incl.drop(['usage'], axis=1), df_incl['usage'].apply(pd.Series)], axis=1)

        df_all = df_incl.merge(df_excl, how='inner', on=['season','id', 'name', 'position', 'team', 'conference'], suffixes=['_incl_gt','_excl_gt'])

        df_all = rename_col(df_all, 'id', 'player_id')
        df_all = rename_col(df_all, 'name', 'player_name')
        
        df_all = self.add_dtstamp_to_df(df_all)

        self.ingest(df_all, 'cfb_player_usage', 'replace')

    def ingest_rankings_old_method(self, current_season_year):

        #if year was passed as int, convert to list of ints
        year_list = make_list(current_season_year)

        #initialize df
        df = pd.DataFrame()
        
        #pull full schedule for every year
        for year_item in year_list:

            #pull rankings data from sports-reference.com 
            #for the given year as large HTML text string
            r = requests.get(
                'https://www.sports-reference.com/cfb/years/' + 
                str(year_item) + 
                '-polls.html'
            ).text

            df_temp = pd.read_html(r)[0]
            df_temp['season'] = year_item
            
            #convert api output from html to dataframe
            #and append to df
            df = df.append(df_temp, sort=True)

        #the table repeats the column headers.  Remove 
        #the repeated headers appearing the table body.
        #To do this, first find the index values in
        #the df where this occurs.
        my_list = list(
            filter(
                None, 
                np.where(
                    df['Date']=='Date',
                    df.index,
                    None
                )
            )
        )

        #drop the index values identified
        df.drop(my_list, axis=0, inplace=True)

        #set week_type as Preseason, Normal, or Final
        df['week_type'] = np.where(
            (df['Date'] == 'Final') |
            (df['Date'] == 'Preseason'),
            df['Date'],
            'Normal'
        )

        #replace 'Final' and 'Preseason' values to dummy values that will sort well
        df['Date'] = np.where(
            df['Date'] == 'Final',
            str(year_item) + '-12-31',
            df['Date']
        )

        df['Date'] = np.where(
            df['Date'] == 'Preseason',
            str(year_item) + '-08-01',
            df['Date']
        )

        df['Wk'] = pd.to_numeric(df['Wk'], errors='coerce').astype(int).round()
        df['season_week'] = df['season']*100 + df['Wk']

        #get the indexes to line up so the data can be 
        #transferred from team_split to df
        team_split = self.__split_team_and_record(df, 'School').reset_index()
        df = df.reset_index()

        #transfer fields from team_split to df
        df['team'] = team_split['team']
        df['record'] = team_split['record']

        win_loss_split = self.__split_wins_and_losses(df, 'record').reset_index()
        df['wins'] = win_loss_split['wins'].astype(int).round()
        df['losses'] = win_loss_split['losses'].astype(int).round()
        
        conf_subconf_split = self.__split_conf_and_subconf(df, 'Conf').reset_index()
        df['conf'] = conf_subconf_split['conf']
        df['subconf'] = conf_subconf_split['subconf']
        
        #df.drop(['Prev','Chng','record'], axis=1, inplace=True)
        
        

        #odd situation arose in week 6 of season 2019 where
        #there were two teams ranked #25. added this line
        #of code to drop the later indexed item for each
        #rank position within each season/week group.
        df = df.drop_duplicates(['Rk','Wk','season'])

        #rename df columns for usability
        df = df.rename(
            columns={
                'Wk':            'week', 
                'Date':          'date',
                'Rk':            'rank',
                'Conf':          'conf',
            }
        )

        #arrange the columns in a particular order
        sorted_cols = [
            'season',
            'week',
            'season_week',
            'date',
            'week_type',
            'School',
            'team',
            'rank',
            'wins',
            'losses',
            'conf',
            'subconf'
        ]
        df = df[sorted_cols]

        #type the columns
        df = df.astype(
            {
                'season': int,
                'week': int,
                'season_week':int,
                'date': str,
                'week_type': str,
                'team': str,
                'rank': int,
                'wins': int,
                'losses': int,
                'conf': str,
                'subconf': str
            }
        )

        df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d", errors='coerce')
        
        df = self.add_dtstamp_to_df(df)

        #self.ingest(df[df['season'] != current_season_year], 'cfb_rankings_hist_temp', 'replace')
        #self.ingest(df[df['season'] == current_season_year], 'cfb_rankings_current_temp', 'replace')
        self.ingest(df, 'cfb_rankings_old_method', 'replace')
        
    def ingest_rankings(self, year_list):
        #if year was passed as int, convert to list of ints
        year_list = make_list(self.year_list)
        #year_list = [2019]

        #initialize df
        df = pd.DataFrame()

        #pull full schedule for every year
        for year_item in year_list:

            #pull rankings data from sports-reference.com 
            #for the given year as large HTML text string
            r = requests.get(
                'https://api.collegefootballdata.com/rankings?year=' + str(year_item) + '&seasonType=both'
            ).json()

            temp = pd.DataFrame(r)

            temp2 = pd.DataFrame(temp['polls'][0])

            temp3 = pd.DataFrame(temp2['ranks'][0])

            full_df = pd.DataFrame()
            for level_1_count in range(temp.index.stop):
                temp2 = pd.DataFrame(temp['polls'].iloc[level_1_count])
                for level_2_count in range(temp2.index.stop):
                    layer_2_df = pd.DataFrame(temp['polls'].iloc[level_1_count])
                    layer_3_df = pd.DataFrame(layer_2_df['ranks'].iloc[level_2_count])

                    layer_3_df['season'] = temp['season'].iloc[level_1_count].astype(int).round()
                    layer_3_df['week'] = temp['week'].iloc[level_1_count].astype(int).round()
                    layer_3_df['poll'] = temp2['poll'].iloc[level_2_count]

                    full_df = full_df.append(layer_3_df, sort=True)

            full_df['season_week'] = full_df['season']*100 + full_df['week']
            full_df['season_week'] = full_df['season_week'].astype(int).round()
            full_df['series'] = np.where(
                (full_df['poll'].apply(lambda x: str(x).find('FCS')) >= 0)
                | (full_df['poll'].apply(lambda x: str(x).find('AFCA')) >= 0),
                'FCS',
                'FBS'
            )

            full_df['series_division'] = full_df['series']
            full_df['series_division'] = np.where(
                (full_df['series_division']=='FCS')
                & (full_df['poll'].apply(lambda x: str(x).find(' II ')) >= 0),
                full_df['series'] + ' D2',
                full_df['series_division']
            )
            full_df['series_division'] = np.where(
                (full_df['series_division']=='FCS')
                & (full_df['poll'].apply(lambda x: str(x).find(' III ')) >= 0),
                full_df['series'] + ' D3',
                full_df['series_division']
            )
            full_df['is_playoff_poll'] = np.where(
                (full_df['poll'].apply(lambda x: str(x).find('Playoff')) >= 0),
                1,
                0
            )
            full_df['series_division'] = np.where(
                (full_df['series_division']=='FCS'),
                'FCS D1',
                full_df['series_division']
            )
            full_df['first_place_votes'] = full_df['firstPlaceVotes']
            full_df['team'] = full_df['school']

            full_df = full_df[[
                'series_division',
                'poll',
                'season',
                'week',
                'season_week',
                'rank',
                'team',
                'conference',
                'first_place_votes',
                'points',
                'is_playoff_poll'
            ]]

            full_df = full_df.sort_values(['series_division','season','week','is_playoff_poll','poll','rank'], ascending=[True, False, False, False, True, True]).reset_index()
            
            df = df.append(full_df, sort=True)
            
            del temp, temp2, temp3, full_df

        df = df.drop(labels=['index'], axis=1)
        
        #arrange the columns in a particular order
        sorted_cols = [
            'series_division',
            'poll',
            'season',
            'week',
            'season_week',
            'rank',
            'team',
            'conference',
            'first_place_votes',
            'points',
            'is_playoff_poll'
        ]
        df = df[sorted_cols]

        df = df.sort_values(['series_division','season','week','is_playoff_poll','poll','rank'], ascending=[True, False, False, False, True, True]).reset_index().drop(labels=['index'], axis=1)
        
        df = df.merge(self.teams, how='left', on='team')
        
        df = reorder_cols(df, [0,1,2,3,4,5,6,11,7,8,9,10])

        df = self.add_dtstamp_to_df(df)

        self.rankings = df
        self.ingest(df, 'cfb_rankings', 'replace')

    def ingest_game_team_stats(self, year_list):
        year_list = make_list(year_list)
        
        r = requests.get('https://api.collegefootballdata.com/games/teams?year=2019&week=10&seasonType=regular&team=Wake%20Forest').json()

        df = pd.DataFrame(r)
        
        full_df = self.__nested_to_df_l3(df, ['id'],'teams', ['school','conference','homeAway','points'],'stats')
        
        full_df = rename_col(full_df, 'id', 'game_id')
        
        full_df = full_df.merge(self.teams, how='left', left_on='school', right_on='team')
        
        full_df = self.add_dtstamp_to_df(full_df)
        
        full_df = drop_col(full_df, 'school')
        full_df = rename_col(full_df, 'stat','stat_value')
        full_df = reorder_cols(full_df, [3,7,6,1,2,4,0,5,8])

        self.game_team_stats = full_df
        self.ingest(full_df, 'cfb_game_team_stats', 'replace')
        
        return full_df

    def ingest_all(self, year_list, current_season_year):
        year_list = make_list(year_list)
        
        self.ingest_teams()
        self.ingest_venues()
        self.ingest_schedule(year_list)
        #self.ingest_rankings_old_method(year_list)
        self.ingest_rankings(year_list)
        self.ingest_talent(year_list)
        self.ingest_player_usage(year_list)
        
        list_of_tables = self.query("select * from information_schema.tables where table_schema = 'sports'")['TABLE_NAME'].tolist()

        for list_item in list_of_tables:
            self.table_to_csv([list_item])
    
    def table_to_csv(self, tables):
        tables = make_list(tables)
        
        for table_item in tables:
            sqlstr = 'SELECT * FROM ' + table_item
            df = self.query(sqlstr)
            
            path = './csv/'
            file = table_item + '.csv'
            df.to_csv(path + file)

    def add_dtstamp_to_df(self, df):
        df['last_updated'] = global_now
        
        return df
        
    def __split_team_and_record(self, df, field_to_split):
        split = df[field_to_split].str.rsplit(' (', n = -1, expand = True)
        split = split.fillna('')

        team_record_split = pd.DataFrame()
        for i, r in split.iterrows():
            team = []
            team.append('')
            record = []
            record.append('')
            if (len(r.index) == 3):
                if (r[2]=='') & (r[1]==''):
                    team[0] = r[0]
                    record[0]='0-0'
                elif r[2].find('-') > -1:
                    team[0]=(r[0] + ' (' + r[1])
                    record[0]=(r[2].replace(')',''))
                elif r[1].find('-') > -1:
                    team[0]=(r[0])
                    record[0]=(r[1].replace(')',''))
                else:
                    team[0]=(r[0] + ' (' + r[1])
                    record[0]=('0-0')
            elif (len(r.index) == 2):
                if (r[1]==''):
                    team[0] = r[0]
                    record[0]='0-0'
                elif r[1].find('-') > -1:
                    team[0]=(r[0])
                    record[0]=(r[1].replace(')',''))
                else:
                    team[0]=(r[0] + ' (' + r[1])
                    record[0]=('0-0')

            row = pd.DataFrame(
                {'team': team,
                 'record': record
                }
            )
            team_record_split = team_record_split.append(row, sort=True)
            del row

        return team_record_split

    def __split_wins_and_losses(self, df, field_to_split):
        win_loss_split = df[field_to_split].str.split('-', n = -1, expand = True)
        win_loss_split = win_loss_split.fillna('')
        win_loss_split.columns = {'losses','wins'}
        return win_loss_split
    
    def __split_conf_and_subconf(self, df, field_to_split):
        conf_subconf_split = df[field_to_split].str.split('(', n=-1, expand=True)
        conf_subconf_split.columns = {'subconf','conf'}
        conf_subconf_split['subconf'] = conf_subconf_split['subconf'].str.replace(')','')
        conf_subconf_split['subconf'] = np.where(
            conf_subconf_split['subconf'].isnull() == True,
            '', 
            conf_subconf_split['subconf']
        )
        return conf_subconf_split

    def test():
        sqlstr = 'SELECT * FROM test02'
        
        df = self.query(sqlstr)

        #'gobble' will append due to not being a valid type
        self.ingest(df, 'test02', 'gobble')

        df = self.query(sqlstr)
        print(df)

    def __nested_to_df_l3(self, df, columns_from_l1, l1_column_to_expand, columns_from_l2, l2_column_to_expand):

        temp2 = pd.DataFrame(df[l1_column_to_expand][0])

        temp3 = pd.DataFrame(temp2[l2_column_to_expand][0])

        full_df = pd.DataFrame()
        for level_1_count in range(df.index.stop):
            temp2 = pd.DataFrame(df[l1_column_to_expand].iloc[level_1_count])
            for level_2_count in range(temp2.index.stop):
                layer_2_df = pd.DataFrame(df[l1_column_to_expand].iloc[level_1_count])
                layer_3_df = pd.DataFrame(layer_2_df[l2_column_to_expand].iloc[level_2_count])

                for col_item in columns_from_l1:
                    layer_3_df[col_item] = df[col_item].iloc[level_1_count]
                for col_item in columns_from_l2:
                    layer_3_df[col_item] = temp2[col_item].iloc[level_2_count]

                full_df = full_df.append(layer_3_df, sort=True)
        full_df = full_df.reset_index().drop(labels=['index'], axis=1)
        return full_df