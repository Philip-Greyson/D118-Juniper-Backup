from __future__ import print_function

import google.auth
import os # needed for environement variable reading
import glob # needed to read list of files in directory
import datetime # needed for current date
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from netmiko import *
from datetime import *

SCOPES = ['https://www.googleapis.com/auth/drive']

username = os.environ.get('JUNIPER_USERAME')
password = os.environ.get('JUNIPER_PASSWORD')



if __name__ == '__main__':
    with open('backupLog.txt', 'w') as log:
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        # get the current date for naming purposes
        date = datetime.now().strftime('%Y-%m-%d') # get todays date in ISO-8601 format
        print(f'INFO: Starting backup for {date}')

        # delete all old .cfg files in the Configs directory so we don't include old data
        oldfiles = glob.glob('Configs/*.cfg')
        for f in oldfiles:
            print(f'ACTION: Removing old config file {f}')
            print(f'ACTION: Removing old config file {f}', file=log)
            os.remove(f)

        # open the input IP file and start going through each IP one at a time
        with open('IPList.txt', 'r') as inputFile:
            IPs = inputFile.readlines() # read all the lines of the file
            for IP in IPs: # go through each IP address
                IP = IP.strip() # strip the newline characters off the IP line
                # set up the connection info using the IP from the file
                switch = {
                    'device_type': 'juniper',
                    'host': IP,
                    'username': username,
                    'password': password,
                    'session_log': 'sessionLog.txt' # also open a session log for debugging
                }
                with ConnectHandler(**switch) as net_connect: # connect with netmiko
                    host = net_connect.send_command('show version | match Hostname:') # just get the host-name portion of the version output
                    host = host.split() # split the host string by the space in the middle and newlines
                    print(f'INFO: Processing {IP} - {host[1]}')
                    print(f'INFO: Processing {IP} - {host[1]}', file=log)
                    filename = 'Configs/' + host[1] + '.cfg' # append a .cfg to the end of the hostname to make a filename
                    with open (filename, 'w') as output:
                        config = net_connect.send_command_timing(command_string='show configuration') # use _timing since its such a long output, it doesnt "find" it properly with the normal send_command
                        print(config, file=output)