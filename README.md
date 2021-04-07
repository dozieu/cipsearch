# cmipsearch
Performs CUCM phone search based on ip address

cmipsearch is a python script that retrieves table data of phones configured on your CUCM based on their ip addresses.
the script presents option to retrieve only registered phones or all phones, and has option to create a csv file of the output if selected.


Overview
===============
cmipsearch is used to access Cisco Unified Communication Manager (CUCM) and performs a phone query.

It is able concurrently access all your single clucter call manager servers from a list and perform a query for phones.
The result of the query are parsed and then converted to panda dataframe from where the search is performed, results aggregated and then presented to user.
user can choose whether registered or non-registerd phones are to be presented, and can also choose to create a csv file of the results.

script uses Paramiko to perform ssh access to the servers
http://www.paramiko.org/

the query results are converted to panda dataframe for further processing
https://pandas.pydata.org/



Hot to use
==============
Install packages on 'requirements.txt'

Update the script's CM_SERVERS variable: this should be set to a list of the ip addresses of your servers that are running the call manager service and involved in phone registration. 
e.g. CM_SERVERS = [10.28.124.35, 10.28.124.36, 10.28.124.37,]

Run script

Enter username and password when prompted: this is the admin account that has CLI access to the cluster of servers

Enter IP address for search when prompted: the search is to find phone where IP address contains the string entered at prompt

Answer 'yes' or 'no' to other prompt questions: questions partaining to presenting registered phones and creating csv file of results

you will the be prompted with "Retrieving please wait...", After which the results will be Presented.

If you entered "yes" to "Create CSV file of results ?", a csv file will be created in same directory with filename "ipphones.csv"pi

Results
=========
You will be presented with a table, column fields are below: 
'DeviceName', ' Ipaddr', ' RegStatus',' RegStatusChg TimeStamp', ' LastActTimeStamp', 'Server', ' Descr'

You may get results for IP search with more than one result or duplicate devicename results.
This could be because phone had de-registered on one server and re-registred on another.
The script will return data for this phone but the results will have different phone status, phone will show to be registered on one server and unreg on the other.

phones will be listed in order from the most resent activity with a callmanger server
order will be based on the ' RegStatusChg TimeStamp' and ' LastActTimeStamp' fields
which are the phones registration status and last active time for the device, so you will be able to tell on which server the phone was last registered.

