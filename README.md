# cfb-data

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
a database to handle record storage and processing.  However, my
preference for a db is MySQL via Workbench, which is currently 
unavailable for my OS (Raspbian Stretch).</p>
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
package installations.  The following packages are used, but were
pre-installed with my python 3.7 installation on Raspbian Stretch:</p>
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
