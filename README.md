# cfb-data

<h1>10/26/2019 SPECIAL NOTE:</h1>
<p>One of the data sources for this project is 
api.collegefootballdata.com which has been taken offline temporarily 
due to a recent hacking incident.  The owner of that API provided 
some information on reddit (link: 
https://www.reddit.com/r/CFBAnalysis/comments/dnjxah/collegefootballdatacom_down_until_further_notice/ ). 
While the data source is offline, I will be focusing on working on 
one of my long-term goals, which is to establish a local database 
and ingestion flow.  As a result, the code will be non-functional 
for some unknown period of time (until the API is back online). 
For reference, the API was taken offline on 10/26/2019 with the 
expectation of it eventually being restored, but timelines are 
not available at the time of writing this note.

<b>Summary:</b>
<p>Python code used to pull data related to FBS college football teams.</p>
<br>

<b>Vision:</b>
<p>I'm building this project on a raspberry pi (4B) with the vision 
of having the device left on permanently and using crontab jobs to 
notify me of college football events that I am interested in (such 
as forward and retrospective schedule or game results information for 
selected teams).</p>

<p>I am initially building in some customizability via a config.ini 
file (read further for more info), including the customizability of 
outgoing email server for notifications. </p>

<p>In the longer run, I would like to use this as stepping stone into
a similar project for college basketball.  I'd also like to implement
a database to handle record storage and processing.  In late October,
I selected MariaDB as the database solution (a MySQL replacement), 
because I am using Raspbian Buster on an ARM architecture which has 
limited my options.  Additionally, I am already familiar with the 
assocaited Python packages used in a MySQL-enabled stack.</p>
<br>

<b>Cloning / Installation:</b>
<p>When cloning this repo, ensure you rename config_template.ini to 
config.ini and populate the values as described in the comments 
in that file.  The code will not function without the necessary 
values.</p>
<br>

<b>Packages / Requirements:</b>
<p>This repo is built to minimize specialty package requirements. 
If I've been successful, the code will not require any special 
package installations to run the <i>notification processes</i>.  The 
following packages are used, but were pre-installed with my 
Python 3.7 installation on Raspbian Stretch:</p>
<li>os
<li>sys
<li>configparser
<li>numpy
<li>pandas
<li>requests
<li>datetime
<li>smtplib
<li>email
<li>dateutil
<br>

<p>Note that as this project progresses into the future, there 
will also be ingestion processes that will be used.  Those
ingestion processes are expected to require the following:</p>
<li>Python packages:
  <ul>
  <li>sqlalchemy
  <li>mysql-connector
  </ul>
<li>Database:
  <ul>
  <li>MySQL or MariaDB database with write access
  <li>A specail dbconfig.ini file to define 
  connection params (not yet created in this 
  project)
  </ul>

<b>This project gratefully leverages the following other projects:</b>
<li>api.collegefootballdata.com for:
  <ul>
  <li>Ingestion of schedule data
  <li>Developer of that API can be found at www.github.com/BlueSCar
  </ul>

<li>www.sports-reference.com for:
  <ul>
  <li>Ranking data
  <li>Developer of that API can be found at: www.github.com/roclark
  </ul>

<br><br>
<b>Go Deacs!</b>
