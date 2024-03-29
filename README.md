# cipsearch
Performs CUCM phone search based on ip address

cipsearch is a python script that retrieves table data of phones configured on your CUCM based on their ip addresses.
the script presents option to retrieve only registered, unregistered or all phones, and has option to create a csv file of the output if selected.


Overview
===============
cipsearch is used to access Cisco Unified Communication Manager (CUCM) and performs a phone query.

It is able to concurrently access call manager servers within a single clucter and perform a CLI query for phones.
The result of the query are parsed and then converted to panda dataframes on which the search is performed. The results are aggregated and then presented to user on screen. User can choose whether to display registered, non-registerd or all phones. User can also choose to create a csv file of the results wheh prompted.

Script uses Paramiko to perform ssh access to the servers
http://www.paramiko.org/

The query results are converted to panda dataframe for further processing
https://pandas.pydata.org/

Try the dockerized web gui version https://hub.docker.com/r/dozieu/collabtools-v01

How to use
==============
Install packages on 'requirements.txt'

On running the script a setup prompt will be presented, user can select 'yes' to setup or 'no' to use previously set credentials.
For the first use, your answer will be 'yes' then enter username and password as prompted, enter list of the IP addresses of your call manager servers; this will be a string of the addresses seperated by  comma, there must be NO spaces as in 
e.g. 10.28.124.35,10.28.124.36,10.28.124.37

    Run script

    Enter credentials:  use previously setup credentials or enter setup

    Enter IP address for search when prompted: the search is to find phone where IP address contains the string entered at prompt

    Answer 'yes' or 'no' to other prompt questions: questions partaining to presenting registered phones and creating csv file of results

    you will the be prompted with "Retrieving please wait...", After which the results will be presented.

    If you entered "yes" to "Create CSV file of results ?", a csv file will be created in same directory with file name "ipphones.csv"

Results
=========
You will be presented with a table, column names are below:

'DeviceName', ' Ipaddr', ' RegStatus',' RegStatusChg TimeStamp', ' LastActTimeStamp', 'Server', ' Descr'

You may get results of IP search with more than one result or duplicate devicename results.
This would be because phone had de-registered on one server and re-registred on another.
You will be able to see the phone registration status and activity timestamp.

Phones will be listed in order from the most resent activity with a callmanger server so you will be able to tell on which server the phone was last registered;
phone order is based on the ' RegStatusChg TimeStamp' and ' LastActTimeStamp' fields which are the phones registration status and last active time for the device. 

