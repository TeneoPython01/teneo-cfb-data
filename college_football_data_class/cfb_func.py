# College Football Functions
#
# Author(s):        TeneoPython01@gmail.com
# Developed:        09/02/2019
# Last Updated:     10/11/2019
#
# Purpose:          This script is used by the college_football_data_class
#                   module for various functions like the API calls
#
# Special Notes:    n/a

import pandas as pd #to handle data in pandas dataframes
pd.set_option('display.max_rows', 1000) #allow printing lots of rows to screen
pd.set_option('display.max_columns', 1000) #allow printsin lots of cols to screen
pd.set_option('display.width', 1000) #don't wrap lots of columns

import requests #to pull JSON data
import numpy as np #to do conditional pandas operations
import datetime as dt #to track datetime stamps
global_now = dt.datetime.now()

#import email functions
import smtplib
import os.path as op
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

from dateutil import tz #for timezone handling with datetime dtypes

#this is the datetime mask native to the API output
api_mask = '%Y-%m-%dT%H:%M:%S.000Z' 
#this is the datetime mask for readable format
readable_mask = "%a %m/%d/%Y %I:%M%p %Z" #this is a readable format
year_mask = "%Y" #just the year
from_zone = tz.tzutc() #API datetimes are in UTC time
to_zone = tz.tzlocal() #Used for converting to local timezone


#FUNCTION RETURNS ALL API SCHEDULE DATA FOR YEAR REQUESTED
def get_full_year_schedule_all_teams(year):

    #pull json data from API
    r = requests.get(
        'https://api.collegefootballdata.com/games?year=' + str(year) + \
        '&seasonType=both'
    ).json()

    #convert from json to df
    df = pd.DataFrame(r)
    
    #sort the data so that the postseason week 1 data is after the regular
    #season final week data
    df = df.sort_values(by=['season','season_type','week'], ascending=[True,False,True])
    
    #convert datetimes to readable format
    df['start_time_dt'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone)
    df['start_time_str'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone).strftime(readable_mask)
    df['start_year_dtper'] = pd.to_datetime(df['start_date'].values, format=api_mask, utc=True).tz_convert(to_zone).tz_convert(None).to_period('Y')
    df['start_year_int'] = df['start_year_dtper'].astype(int) + 1970
    
    return df


#FUNCTION RETURNS THE FOUR DIGIT INTEGER YEAR BASED ON THE
#CURRENT SYSTEM DATE.
def get_current_year():
    return int(dt.datetime.now().year)

#FUNCTION RETURNS THREE OUTPUTS IN TUPLE:
#1) EIGHT DIGIT INTEGER DATE IN YYYYMMDD FORMAT
#2) SIX DIGIT INTEGER TIME IN HHMMSS FORMAT
#4) FIFTEEN CHARACTER STRING IN 'YYYYMMDD_HHMMSS' FORMAT
def get_current_datetime_int():
    date_int = global_now.year*10000 + global_now.month*100 + global_now.day
    time_int = global_now.hour*10000 + global_now.minute*100 + global_now.second
    date_time_string = str(date_int) + '_' + str(time_int)
    return date_int, time_int, date_time_string

#FUNCTION RETURNS HTML CODE FOR THE HEADER PORTION OF
#AN HTML FILE
def html_header(my_title=''):
    html_script = """
    <!DOCTYPE html>
    <HTML>
        <HEAD>
            <TITLE>"""
    
    html_title = my_title + '</TITLE>'
    
    html_script = html_script + '\n' + html_title    
    
    return html_script

#FUNCTION RETURNS HTML CODE FOR THE STYLE TAG PORTION OF
#AN HTML FILE
def html_style_header():

    html_script = """
    <!-- CSS goes in the document HEAD or added to your external stylesheet -->
    <style type="text/css">
    table.gridtable {
        font-family: verdana,arial,sans-serif;
        font-size:11px;
        border-width: 1px;
        border-color: #666666;
        border-collapse: collapse;
    }
    table.gridtable th{
        border-width: 1px;
        padding: 18px;
        border-style: solid;
        border-color: #666666;
        background-color: #dedede;
    }
    table.gridtable td{
        border-width: 1px;
        padding: 6px;
        border-style: solid;
        border-color: #666666;
        background-color: #ffffff;
    }
    /* Define the default color for all the table rows */
    .gridtable tr{
        background: #b8d1f3;
    }
    /* Define the hover highlight color for the table row */
    .gridtable td:hover {
        background-color: #ffff99;
    }

    </style>
    </HEAD>
    """
    
    return html_script

#FUNCTION RETURNS HTML CODE FOR A DATAFRAME THAT IS
#PASSED AS A PARAMETER AND ASSIGNS THE TABLE
#CLASS NAME TO MATCH THE STYLE TAG CLASS NAME
def html_from_df(df):

    html_script = df.to_html(index=False).replace(
        '<table border="1" class="dataframe">',
        '<table class="gridtable">'
    )
    
    return html_script

#FUNCTION RETURNS HTML CODE FOR THE FOOTER PORTION OF
#AN HTML FILE
def html_footer():

    html_script = """
    </BODY>
    </HTML>
    """
    
    return html_script

#FUNCTION RETURNS HEADER, STYLE TAG, DATAFRAMES, AND FOOTER
#HTML CODE IN ONE CONCATENATED STRING
def df_to_html(my_title, df):

    html_script = ''
    html_script = html_script + html_header(my_title)
    html_script = html_script + html_style_header()
    html_script = html_script + html_from_df(df)
    html_script = html_script + html_footer()
    
    return html_script

#FUNCTION SENDS MAIL
#PARAMS:
#    SEND_FROM: A STRING CONTAINING THE EMAIL ADDRESS
#        OF THE SENDER
#    SEND_TO: CAN BE A STRING OR A LIST OF STRINGS
#        CONTAINING EMAIL ADDRESSES FOR RECIPIENTS
#    SUBJECT: A STRING
#    MESSAGE: A STRING
#    FILES: A STRING OR A LIST OF STRINGS THAT
#        CONTAINS THE PATH AND FILENAME OF EACH
#        ATTACHMENT
#    SERVER: A STRING WITH THE SERVER ADDRESS
#    PORT: AN INTEGER
#    USERNAME: A STRING OF THE EMAIL USERNAME
#    PASSWORD: A STRING OF THE EMAIL PASSWORD
#    USE_TLS: BOOLEAN
#USAGE:
#sendmail('emailaddr@gmail.com', recipient_list,
#         message_body_str, subject_str, file_list,
#         'smtp.gmail.com', 587, my_username,
#         my_password, True)
def sendmail(send_from, send_to, subject, message, 
             files, server="localhost", port=587, 
             username='', password='', use_tls=True):

    #if the send_to param is a list, then convert
    #to a string with a specific format to enable
    #sending to multiple recipients
    if type(send_to) is list:
        send_to = ' , '.join(send_to)
    
    #if the files param is not a list, then
    #convert it into a list
    if type(files) is not list:
        files = [ files ]

    #create MIME object and assign attributes
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'html'))

    #attach the file(s) (if any)
    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(op.basename(path)))
        msg.attach(part)

    #create the SMTP object and assign attributes
    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()

    #log into mail account and send email
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to.split(','), msg.as_string())

    #close the SMTP connection
    smtp.quit()

#FUNCTION RETURNS ALL RANKING DATA FOR YEAR REQUESTED
def get_rankings_all_weeks(year):
    
    #pull rankings data from sports-reference.com 
    #for the given year as large HTML text string
    r = requests.get(
        'https://www.sports-reference.com/cfb/years/' + 
        str(year) + 
        '-polls.html'
    ).text

    #load the HTML table data into pandas dataframe
    df = pd.DataFrame()
    df = pd.read_html(r)[0]

    #the table repeats the column headers.  Remove 
    #the repeated headers appearing the table body.
    #To do this, first first the index values of
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


    #ranking change is in absolute values, so
    #recalculate it. to do this, we have to
    #convert Rk (current ranking) and Prev
    #(last week's ranking) to numerics. we
    #also have to handle for teams that go
    #from unranked to ranked (jump at least
    #25 positions).
    df['Prev'] = pd.to_numeric(df['Prev'], errors='coerce').fillna(26).astype(int).round()
    df['Rk'] = pd.to_numeric(df['Rk'], errors='coerce').fillna(26).astype(int).round()
    df['Chng'] = df['Prev'] - df['Rk']
    df['Chng'] = df['Chng'].astype(int).round()
    if 'This Week' in df.columns:
        df.drop('This Week', axis=1, inplace=True)

    #table data stuffs the team and the team record
    #into a single column.  this code separates
    #them into two columns.  when record data doesn't
    #exist (week 1 preseason ranking data) then show
    #an empty string.
    split = df["School"].str.split("(", n = 1, expand = True)
    #sometimes there are leading/trailing spaces to be removed
    df['School'] = split[0].apply(lambda x: x.strip())
    #record is always 0-0 when preseason rankings come out
    #prior to week 1 games, so fillna with 0-0 records.
    split[1] = split[1].fillna('(0-0)')
    #sometimes there are leading/trailing spaces to be removed
    df['School Record'] = split[1].apply(lambda x: x.strip())
    #this line might be redundant / removable:
    df['School Record'] = df['School Record'].fillna('')

    #table data shows the conference including the
    #subconference. This code separates them into
    #separate columns.  e.g. ACC and Atlantic vs
    #Coastal; or SEC East vs West.  When a conference
    #doesnt have a subconf, show an empty string.
    split = df["Conf"].str.split("(", n = 1, expand = True)
    #sometimes there are leading/trailing spaces to be removed
    df['Conf'] = split[0].apply(lambda x: x.strip())
    #fillna with empty string prevents NoneType error when
    #no sub conf exists
    split[1] = split[1].fillna('')
    df['Conf Sub'] = split[1].apply(lambda x: x.strip())
    #this line might be redundant / removable:
    df['Conf Sub'] = df['Conf Sub'].fillna('')
    
    #retype week column to integer
    df['Wk'] = pd.to_numeric(df['Wk'], errors='coerce').astype(int)
    
    #rename df columns for usability
    df = df.rename(
        columns={
            'Wk':            'week', 
            'Date':          'date',
            'Rk':            'rank',
            'School':        'team',
            'Prev':          'prev_rank',
            'Chng':          'rank_chg',
            'Conf':          'conf',
            'School Record': 'record',
            'Conf Sub':      'sub_conf',
            'season':        'season'
        }
    )

    #set season to the year
    df['season'] = year

    #set week_type as Preseason, Normal, or Final
    df['week_type'] = np.where(
        (df['date'] == 'Final') |
        (df['date'] == 'Preseason'),
        df['date'],
        'Normal'
    )

    #replace 'Final' and 'Preseason' values to dummy values that will sort well
    df['date'] = np.where(
        df['date'] == 'Final',
        str(year) + '-12-31',
        df['date']
    )
    df['date'] = np.where(
        df['date'] == 'Preseason',
        str(year) + '-06-01',
        df['date']
    )
    df['season_week'] = df['season']*100 + df['week']

    #odd situation arose in week 6 of season 2019 where
    #there were two teams ranked #25. added this line
    #of code to drop the later indexed item for each
    #rank position within each season/week group.
    df = df.drop_duplicates(['rank','week','season'])
    
    #arrange the columns in a particular order
    sorted_cols = [
        'season',
        'week',
        'season_week',
        'date',
        'week_type',
        'team',
        'rank',
        'prev_rank',
        'rank_chg',
        'conf',
        'sub_conf',
        'record'       
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
            'prev_rank': int,
            'rank_chg': int,
            'conf': str,
            'sub_conf': str,
            'record': str
        }
    )
    
    # TEMP FIX FOR PLAYOFF RANKING WEEK MISMATCH
    df['week'] = df['week'] + 10
    df['season_week'] = df['season_week'] + 10
    
    return df

def get_poll_data(year):
    #pull rankings data from sports-reference.com 
    #for the given year as large HTML text string
    r = requests.get(
        'https://api.collegefootballdata.com/rankings?year=' + str(year) + '&seasonType=both'
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


    full_df = full_df.sort_values(
        ['series_division','season','week','is_playoff_poll','poll','rank'], 
        ascending=[True, False, False, False, True, True]
    ).reset_index()

    #print(full_df)

    #db.ingest(full_df, 'cfb_rankings_c', 'replace')\
    
    return full_df
