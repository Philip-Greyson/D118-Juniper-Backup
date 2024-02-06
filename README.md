
# D118-Juniper-Backup

Script to backup Juniper switch configs via netmiko and upload them to a folder inside a shared drive in Google Drive via the API.

## Overview

The script first clears out any old config files stored in the "Configs" folder in the program directory. Then it does its setup in Google Drive, searching for the specified Drive folder name inside the specified shared drive (by ID), and creates a daily folder inside the parent folder. If the specified Drive folder name parent is not found, it will create it as well as the daily folder.
Then the list of IPs is parsed from the text file, and each IP is used with netmiko to SSH into the switch. The "show version" command is used to get the hostname of each switch, and then the "show configuration" output is exported into a file named after the switch's hostname.cfg and placed in the "Configs" folder. While the file extension is .cfg, it is just a plain text format.
After each IP is processed, each file in the "Configs" folder is uploaded to the daily Drive folder created earlier, one at a time.

## Requirements

The following Environment Variables must be set on the machine running the script:

- JUNIPER_USERNAME
- JUNIPER_PASSWORD

These are fairly self explanatory, and just relate to the username and passwords for the Juniper switches (assuming they all can be logged in to with the same username/password). If they have multiple usernames and passwords you will need to change a bulk of the script in the SSH section. If you wish to directly edit the script and include these credentials, you can.

**You will need to provide a plaintext file that contains the IP addresses** of the switches, one per line. By default this file should be named "IPList.txt" (see customization below for other names) and will contain IP addresses like "192.168.0.1".
**You will also need to create a directory inside the script parent directory named "Configs"**. This is just a folder that holds the resulting config files.
**You will need to provide an ID for the Shared Drive (or other drive folder)**, explanation on how to find this can be found in the customization section below.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Netmiko](https://github.com/ktbyers/netmiko?tab=readme-ov-file#installation)
- [Python-Google-API](https://github.com/googleapis/google-api-python-client#installation)

In addition, an OAuth credentials.json file must be in the same directory as the overall script. This is the credentials file you can download from the Google Cloud Developer Console under APIs & Services > Credentials > OAuth 2.0 Client IDs. Download the file and rename it to credentials.json. When the program runs for the first time, it will open a web browser and prompt you to sign into a Google account that has the permissions to disable, enable, deprovision, and move the devices. Based on this login it will generate a token.json file that is used for authorization. When the token expires it should auto-renew unless you end the authorization on the account or delete the credentials from the Google Cloud Developer Console. One credentials.json file can be shared across multiple similar scripts if desired. There are full tutorials on getting these credentials from scratch available online. But as a quickstart, you will need to create a new project in the Google Cloud Developer Console, and follow [these](https://developers.google.com/workspace/guides/create-credentials#desktop-app) instructions to get the OAuth credentials, and then enable APIs in the project (the Drive API is used in this project).

You must have a Google account that has the proper roles and privileges to access and upload to the shared drive that you will be using. This is the account that the script will run "as", and it will need to be signed into the first time the script is run after the credentials.json file is added. It should pop up a web browser automatically and prompt you to sign in, then the token.json file is created in the directory after the sign-in process completes that it uses from then on to authenticate.

## Customization

This script should be able to be easily customized to fit most use cases, as long as Juniper switches are used and you have access to a shared drive. The biggest things you ***must*** customize:

- `SHARED_DRIVE_ID` is the Google ID for the shared drive that will house the configs parent folder. This can be found in one of two ways, either by navigating to it on the web through drive.google.com and then looking in the URL bar for the last section, see [here](https://robindirksen.com/blog/where-do-i-get-google-drive-folder-id) for an example. There is also a bit of code that should find all shared drives you have access to, though it does not seem to always list every drive, so I would recommend just using the URL method.
- You must comment/uncomment the lines that define `filename = config.split('/')[1]` depending on your host OS. By default, the Linux version is enabled. Linux needs to have the / used, Windows uses \ for its paths so that must be used (with an extra \ as an escape character), so simply comment out the Linux line and uncomment the Windows one.

Then there are some things you might want to customize to better suit your use:

- `IP_LIST_FILE` is the name of the file in the same directory as the script that contains your IP addresses. If this needs to be different for whatever reason, you can change this near the top of the script.
- `DRIVE_FOLDER_NAME` is the name that the "parent" folder will have inside of the shared drive. By default it is 'Juniper Switch Configs', but can be changed to your liking by editing the constant near the top of the script. The daily folders will be created inside of this folder and have the current date in ISO-8601 (YYYY-MM-DD) format. If you want to change that format, edit the `datetime.now(strftime())` section of the script.
