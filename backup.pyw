"""Script to backup Juniper switch configurations and upload them to a folder in Google Drive.

https://github.com/Philip-Greyson/D118-Juniper-Backup

Clears out the old configs from the local folder first, checks and creates the daily in Google Drive under the configured drive folder name.
Then gets the list of IPs from the local file, goes through each device one at a time, gets their hostname and prints out the configuration to a file named after their hostname.
Then takes each file and uploads them to the folder matching today's date in the configured drive folder name
"""

#from __future__ import print_function

import datetime  # needed for current date
import glob  # needed to read list of files in directory
import os  # needed for environement variable reading
from datetime import *

# import google.auth
# import netmiko
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from netmiko import ConnectHandler

SCOPES = ['https://www.googleapis.com/auth/drive']

SWITCH_USERNAME = os.environ.get('JUNIPER_USERNAME')
SWITCH_PASSWORD = os.environ.get('JUNIPER_PASSWORD')
IP_LIST_FILE = 'IPList.txt'
SHARED_DRIVE_ID = '0AHXBA7DxIPfDUk9PVA'
DRIVE_FOLDER_NAME = 'Juniper Switch Configs'


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
        date = datetime.now().strftime('%Y-%m-%d')  # get todays date in ISO-8601 format
        print(f'INFO: Starting backup for {date}')

        # delete all old .cfg files in the Configs directory so we don't include old data
        oldfiles = glob.glob('Configs/*.cfg')
        for f in oldfiles:
            print(f'ACTION: Removing old config file {f}')
            print(f'ACTION: Removing old config file {f}', file=log)
            os.remove(f)

        # to find the ID of the shared drive, use the code below
        # drives = service.drives().list().execute()
        # drives = drives.get('drives',[])
        # for drive in drives:
        #     print(drive)

        # search for the parent folder of "Juniper Switch Configs" either in a shared drive or in the personal drive
        JuniperFolders = service.files().list(corpora='drive',driveId=SHARED_DRIVE_ID,includeItemsFromAllDrives=True,supportsAllDrives=True,q="mimeType='application/vnd.google-apps.folder' and name='"+ DRIVE_FOLDER_NAME +"'").execute()  # execute the search for the parent folder within the specific shared drive
        # JuniperFolders = service.files().list(corpora='user',q="mimeType='application/vnd.google-apps.folder' and name='Juniper Switch Configs'").execute() # for personal drive and not shared drive
        JuniperFolders = JuniperFolders.get('files',[])
        if JuniperFolders:  # check and see if the parent folder exists
            juniperFolderName = JuniperFolders[0].get('name')
            juniperFolderID = JuniperFolders[0].get('id')
            print(f'INFO: Found folder with name "{juniperFolderName}" and ID: {juniperFolderID}')
            print(f'INFO: Found folder with name "{juniperFolderName}" and ID: {juniperFolderID}', file=log)
            # now search for a folder that is just named with todays date, if it exists we can just use it, otherwise create it
            todaysFolder = service.files().list(corpora='drive',driveId=SHARED_DRIVE_ID,includeItemsFromAllDrives=True,supportsAllDrives=True,q="mimeType='application/vnd.google-apps.folder' and name='" + date + "'").execute()
            # todaysFolder = folders = service.files().list(corpora='user',q="mimeType='application/vnd.google-apps.folder' and name='" + date + "'").execute()
            todaysFolder = todaysFolder.get('files',[])
            if todaysFolder:  # check to see if todays date folder already exists
                todaysFolderName = todaysFolder[0].get('name')
                todaysFolderID = todaysFolder[0].get('id')
                print(f'INFO: Found folder with name "{todaysFolderName}" and ID: {todaysFolderID}')
                print(f'INFO: Found folder with name "{todaysFolderName}" and ID: {todaysFolderID}', file=log)
            else:
                juniperParentID = [juniperFolderID]  # make an array that just has the id of the parent juniper folder in it since the argument needs to be passed as an array
                print(f'ACTION: Folder {date} does not exist, will create')
                print(f'ACTION: Folder {date} does not exist, will create', file=log)
                try:
                    file_metadata = {'name': date, 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : juniperParentID, 'driveId' : SHARED_DRIVE_ID}  # define the parents, the team driveID, and the fact its a folder
                    # file_metadata = {'name': date, 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : juniperParentID} # just for personal drive
                    todaysFolder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()  # do the creation of the today folder within the parent folder and on the team drive
                    # todaysFolder = service.files().create(body=file_metadata, fields='id').execute() # for personal drives
                    todaysFolderName = todaysFolder.get('name')
                    todaysFolderID = todaysFolder.get('id')
                    print(f'ACTION: Folder {date} created with ID {todaysFolderID}')
                    print(f'ACTION: Folder {date} created with ID {todaysFolderID}', file=log)
                except Exception as er:
                    print(f'ERROR while creating daily folder "{date}" inside of parent folder "{juniperFolderName}": {er}')
                    print(f'ERROR while creating daily folder "{date}" inside of parent folder "{juniperFolderName}": {er}', file=log)
        else:
            print(f'WARN: No parent folder "{DRIVE_FOLDER_NAME}" found, will try to create. Run the script again to properly backup config files')
            print(f'WARN: No parent folder "{DRIVE_FOLDER_NAME}" found, will try to create. Run the script again to properly backup config files', file=log)
            try:
                # create the new Juniper Switch Configs folder
                driveParentID = [SHARED_DRIVE_ID]
                file_metadata = {'name':DRIVE_FOLDER_NAME, 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : driveParentID, 'driveId' : SHARED_DRIVE_ID}
                # file_metadata = {'name':'Juniper Switch Configs', 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : driveParentID} # for personal drive
                folder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()  # do the creation of the parent folder on the team drive
                # folder = service.files().create(body=file_metadata, fields='id').execute() # for personal drive
                folderID = folder.get('id')
                print(f'ACTION: Folder "{DRIVE_FOLDER_NAME}" created with ID {folderID}')
                print(f'ACTION: Folder "{DRIVE_FOLDER_NAME}" created with ID {folderID}', file=log)
            except Exception as er:
                print(f'ERROR while creating parent folder "{DRIVE_FOLDER_NAME} in parent shared drive with ID {driveParentID}: {er}')
                print(f'ERROR while creating parent folder "{DRIVE_FOLDER_NAME} in parent shared drive with ID {driveParentID}: {er}', file=log)
            # then do the creation of the daily folder inside this new folder
            try:
                juniperParentID = [folderID]  # make an array that just has the id of the parent folder in it since the argument needs to be passed as an array
                print(f'ACTION: Folder {date} does not exist, will create')
                print(f'ACTION: Folder {date} does not exist, will create', file=log)
                file_metadata = {'name': date, 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : juniperParentID, 'driveId' : SHARED_DRIVE_ID}  # define the parents, the team driveID, and the fact its a folder
                # file_metadata = {'name': date, 'mimeType' : 'application/vnd.google-apps.folder', 'parents' : juniperParentID} # just for personal drive
                todaysFolder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()  # do the creation of the today folder within the parent folder and on the team drive
                # todaysFolder = service.files().create(body=file_metadata, fields='id').execute() # for personal drives
                todaysFolderName = todaysFolder.get('name')
                todaysFolderID = todaysFolder.get('id')
                print(f'ACTION: Folder {date} created with ID {todaysFolderID}')
                print(f'ACTION: Folder {date} created with ID {todaysFolderID}', file=log)
            except Exception as er:
                print(f'ERROR while creating daily folder "{date}" inside of parent folder "{DRIVE_FOLDER_NAME}": {er}')
                print(f'ERROR while creating daily folder "{date}" inside of parent folder "{DRIVE_FOLDER_NAME}": {er}', file=log)

        # open the input IP file and start going through each IP one at a time
        with open(IP_LIST_FILE, 'r') as inputFile:  # noqa: UP015
            IPs = inputFile.readlines()  # read all the lines of the file
            for IP in IPs:  # go through each IP address
                try:
                    IP = IP.strip()  # strip the newline characters off the IP line
                    # set up the connection info using the IP from the file
                    switch = {
                        'device_type': 'juniper',
                        'host': IP,
                        'username': SWITCH_USERNAME,
                        'password': SWITCH_PASSWORD,
                        'session_log': 'sessionLog.txt'  # also open a session log for debugging
                    }
                    with ConnectHandler(**switch) as net_connect:  # connect with netmiko
                        host = net_connect.send_command('show version | match Hostname:')  # just get the host-name portion of the version output
                        host = host.split()  # split the host string by the space in the middle and newlines
                        print(f'INFO: Processing {IP} - {host[1]}')
                        print(f'INFO: Processing {IP} - {host[1]}', file=log)
                        filename = 'Configs/' + host[1] + '.cfg'  # append a .cfg to the end of the hostname to make a filename
                        with open (filename, 'w') as output:
                            config = net_connect.send_command_timing(command_string='show configuration')  # use _timing since its such a long output, it doesnt "find" it properly with the normal send_command
                            print(config, file=output)
                except Exception as er:
                    print(f'ERROR on {IP} - {er}')
                    print(f'ERROR on {IP} - {er}',file=log)
        # go through all the .cfg files and upload them to the google drive folder we got the ID from at the beginning
        configs = glob.glob('Configs/*.cfg')
        for config in configs:
            try:
                filename = config.split('/')[1]  # linux
                # filename = config.split('\\')[1] # windows
                parentsArray = [todaysFolderID]
                print(f'ACTION: Uploading {filename} to Google Drive Folder {todaysFolderID}')
                print(f'ACTION: Uploading {filename} to Google Drive Folder {todaysFolderID}', file=log)
                file_metadata = {'name' : filename, 'parents' : parentsArray, 'driveID' : SHARED_DRIVE_ID}
                # file_metadata = {'name' : filename, 'parents' : parentsArray} # for personal drive
                media = MediaFileUpload(filename=config,mimetype='application/octet-stream',resumable=True)  # create the media body for the file, which is the file, file type, and wether it is resumable
                file = service.files().create(body=file_metadata, media_body=media,fields='id',supportsAllDrives=True).execute()  # do the creation of the file using previoulsy defined bodies
                # file = service.files().create(body=file_metadata, media_body=media,fields='id').execute() # for personal drives
                print(F'INFO: Resulting File ID: {file.get("id")}')  # print out the resulting file ID
                print(F'INFO: Resulting File ID: {file.get("id")}', file=log)  # print out the resulting file ID
            except Exception as er:
                print(f'ERROR while trying to upload {filename} to the folder {todaysFolderName} which has ID {todaysFolderID}, check to make sure the filename is parsed correctly: {er}')
                print(f'ERROR while trying to upload {filename} to the folder {todaysFolderName} which has ID {todaysFolderID}, check to make sure the filename is parsed correctly: {er}', file=log)
