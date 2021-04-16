#!/usr/bin/env python

import paramiko
import getpass
import pyinputplus as pyip
import time
from datetime import datetime
import pandas as pd
from io import StringIO
import concurrent.futures
import tracemalloc
import shelve

'''Performs CUCM phone search based on ip address.
The script presents option to retrieve only registered, unregistered or all phones, 
and has option to create a csv file of the output if selected.'''


# ------------------------------------------------------------------------

CMD = 'show risdb query phone\n'

def run_setup():
    # for persistent data; saves and retrieves user credentials
    # Will prompt user for credentials and for servers running call manager service
    # enter servers seperated by comma "," no spaces e.g. 10.10.10.1,10.10.10.2,10.10.10.3
    
    st_setup = pyip.inputYesNo('\nEnter setup ? (yes or no): ')
    setup_var = shelve.open('cli_var')

    if st_setup == 'yes':
        usern = input('username: ')
        pphrase = getpass.getpass('password: ')
        servers = pyip.inputStr("Enter server IP's seperated by comma ',' :")
        servers = servers.split(',')        
        setup_var['cli_user'] = usern
        setup_var['cli_pw'] = pphrase
        setup_var['servers'] = servers
        setup_var.close()
        
    else:
        if ('cli_user' in setup_var) and ('cli_pw' in setup_var):
            print('Using saved credentials')
            usern = setup_var['cli_user']
            pphrase = setup_var['cli_pw']
            servers = setup_var['servers']
            setup_var.close()

    return usern, pphrase, servers


def access_cucm(host, username, password, cmd, port=22, prompt='admin:'):
    # Sends command to cucm cli and recieve cli output, returns cli output 
    recv_data = ''
    try: # initiate connection client and connect
    	connectssh = paramiko.SSHClient() 
    	connectssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    	connectssh.connect(host, port, username, password, timeout=10)
    	time.sleep(.5)
    	rem_conn = connectssh.invoke_shell()

    	while True: # wait for prompt
    	    time.sleep(1)
    	    recv_output = rem_conn.recv(8000).decode()
    	    if prompt == recv_output[-6:]:		        
    	        break
    	    else:
    	        pass
               
    	rem_conn.send(cmd) # send command

    	while True: # recieve till prompt
    	    time.sleep(1)
    	    recv_output = rem_conn.recv(10000000).decode()
    	    recv_data += recv_output
    	    if prompt == recv_output[-6:]:
    	    	break
    	    	
    	connectssh.close()
    except Exception as exc:
        recv_data = ''
        
    return recv_data


def rmv_head_tail(data):
    ''' Removes the table title header and trailer info from cli results'''
    try:
        data = str(data)
        datastr = data.split('\n')
        del datastr[0:6]
        del datastr[-6:]
        
        return datastr
    except Exception as exc:
        print(f'Error with head and tail removal: {exc}')
    return ('')


def fix_row(row):
    ''' Edits row to resolve issues with table such as extra field for webex devices 
        and extra comma's possible in description field. Columns need to be consistent for CSV
        to be represented as uniform table or dataframe '''
    try:
        if 'Automatically created by Webex Hybrid Call Service' in row:
            fix = row.replace('unknown, 0', 'unknown')
        else:
            split_row = row.rsplit(',', 24)
            ip_to_end = ','.join(split_row[-24:])    
            dev_descr = split_row[0].split()
            dev_name = dev_descr.pop(0)
            descr = (' '.join(dev_descr)).replace(',' , ' ')
            new_dev_descr = dev_name + descr
            fix = new_dev_descr + ',' + ip_to_end
        return(fix)
    except Exception as exc:
        print(f'Error while fixing row: {exc}')

    return ('')


def prepare_table(data):
    ''' Checks and corrects for inconsistent table columns '''
    try:
        datastr = rmv_head_tail(data)
        
        for row in datastr:
            line = datastr.index(row)
            if row.count(',') > 25:
                row = fix_row(row)
                if row.count(',') > 25:
                    raise Exception ('error: unable to fix row')
                datastr[line] = row

        datastr = '\n'.join(datastr)
        return datastr
    except Exception as exc:
        print(f'Error with table data: {exc}')
    return ('')


def print_accessing(srvlist):
    ''' Prints servers that are going to be accessed '''
    for serv in srvlist:
        time.sleep(1)
        print('-> '+ str(serv))
    print()


def ask_search_ip():    # get ip address to search 
    get_ip = input('Enter IP address to search: ')
    time.sleep(1)
    print(f'\nFind Phone where IP address contains: {get_ip}')
    return get_ip


def ask_reg_status():    #choose phone status to display
    print('\nSelect Phone status, ', end='')
    ask = pyip.inputMenu(['Registered', 'Unregistered' , 'All'], numbered=True)
    if ask == 'Registered':
        registered = ' reg'
    if ask == 'Unregistered':
        registered = ' unr'
    if ask == 'All':
        registered = 'All'
    
    return registered


def ask_to_makefile():	
	ask = pyip.inputYesNo('\nCreate CSV file of results ? (yes or no): ')
	if ask.lower() == 'yes':
		makecsv = True
	else:
		makecsv = False
	return makecsv


def concurrent_access(fxn, obj_lst, username,password,cmd):
    # Performs concurrent access of servers and executes phone query command
    # asks for search ip address, registered phone, and wether to make csv file
    srv_echo = obj_lst
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = {i: (executor.submit(fxn, i, username,
                                       password,cmd)) for i in obj_lst}

        print_accessing(srv_echo)

        srch_ip = ask_search_ip()

        reg_ph = ask_reg_status()

        mk_csv = ask_to_makefile()

        print('\nRetrieving please wait...')        

    return (results, srch_ip, mk_csv, reg_ph)


def check_results(srv_dict):
    # check for failed ssh connection by checking result of futures
    # retrieves the value of futures and checks if it is an empty string
    # returns check status and converted results
    check = False
    for srv in srv_dict:
        data = srv_output[srv].result()
        if data == '':                
            break
        else:
            check = True
            srv_dict[srv] = data

    return check, srv_dict


def pd_search(srv_dict, ip_addr, reg):
    ''' Converts csv string to dataframe
        performs search for ip address and returns dataframe of results of search'''
    try:
        df_agg = pd.DataFrame()
        for srv in srv_dict: # goes through dictionary converting values to dataframes and searches them
            data = StringIO(srv_dict[srv])
            df = pd.read_csv(data)
            # setting filter based on response
            if reg == ' reg': # this will also catch partially registered phones
                filt = ((df[' Ipaddr'].str.contains(ip_addr, na=False)) & (df[' RegStatus'].str.contains('reg')))                
            if reg == ' unr':
                filt = ((df[' Ipaddr'].str.contains(ip_addr, na=False)) & (df[' RegStatus'] == ' unr'))
            if reg == 'All':
                filt = (df[' Ipaddr'].str.contains(ip_addr, na=False))
            df['Server'] = srv # setting 'Server' column with server name
            df_search = (df.loc[filt, ['DeviceName', ' Ipaddr', ' RegStatus',' RegStatusChg TimeStamp', ' LastActTimeStamp', 'Server', ' Descr']])
            df_agg = df_agg.append(df_search, ignore_index=True) # aggregate results of the search to dataframe

        #print(df_agg)
    except Exception as exc:
        print(f'Panda Error : {exc}')

    return (df_agg)

# ----------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    tracemalloc.start()
    

    try:       

        print('\n---------- Running CUCM IP Searcher ----------\n')
        
        username, password, cm_servers = run_setup()
        print('Accessing..')
        print(cm_servers)

       
        # Get input for seacrhing and presenting search result
        ip_search = concurrent_access(access_cucm, cm_servers, username, password, CMD)    
        print() 
        srv_output = ip_search[0]
        ip_addr = ip_search[1]
        make_csv = ip_search[2]
        reg_only = ip_search[3]

                
        access, result = check_results(srv_output) # -- check for failed ssh access attempts        
        if access == True:
        # Prepare cucm cli output string to be converted to dataframe
            srv_output = result
            for server in srv_output:
                srv_output[server] = (prepare_table(srv_output[server]))

            
            # Convert to dataframe, search and present results   
            results_df = pd_search(srv_output, ip_addr, reg_only)                          
            results_df = results_df.sort_values(by=['DeviceName', ' LastActTimeStamp'], ascending=True)
            total =  results_df.shape[0]  
            print(results_df.to_string(index=False))    
            
            if make_csv == True:
                results_df.to_csv('ipphones.csv', index=False)

            print(f'\nTotal found: {total}')

        else:
            print('Error: Issue with address information or access credentials')

    except Exception as exc:
        print(f'Error : {exc}')
        print('Exiting..')

    # -- end --        
    print('Done')
        
    peak = (tracemalloc.get_traced_memory())[1]    
    print('Peak Memory usage: ' + str(peak) + ' bytes')
    done = input('Hit Enter to Quit!')
    
   
