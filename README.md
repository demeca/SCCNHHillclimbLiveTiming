# SCCNH Hillclimb LiveTiming

The goal of this Python script is to ingest live timing data and output files that can be hosted in an S3 bucket. This allows drivers and spectators to know how participants are doing throughout the day. This could be adapted to work with other systems, but our software uses a sqlite3 DB with a different file for each event in one directory.

## Installation

Python 3.6 or higher is required to be installed. The script is tested with python 3.9.2.
```
pip install -r requirements.txt
```

## Setup

Copy the `example_config.py` file to `config.py` and edit the lines in the file.  
Event path, outDir, and the s3 bucket name must be changed at a minimum.  

All paths must use the `c:/path/to/my/event/folder` notation instead of backslashs (`c:\path\`). This will work on Linux and Windows devices and you will have issues opening the files otherwise.

Make sure to install the AWS CLI if your usecase needs it(https://awscli.amazonaws.com/AWSCLIV2.msi) and configure it. I recommend adding an additional IAM user with programmatic access just for this use case.  

Setup the AWS CLI by running:
```
aws configure
```
and folowing the prompts to input your access key, secret key, and region (`us-east-1` in my case)

If you would like to include a favicon and logo, make sure to edit those lines in the `basehtmlHeader.html` file.

## Usage

Run the script interactively via command line:

```
python timing.py
```

If you know what event you want to serve pass it on the command line with the -e or --event option. Below serves event file 3.

```
python timing.py -e 3
```

If you just want to use the last modified event, use the --latest, -l option. This will often be your easiest option for automation.

```
python timing.py -l
```

## Running via Scheduled Task on Windows

This can be run via scheduled tasks. Python was installed in the path for my setup, so I created a schedule with the following parameters:
- Name: Hillclimb Live
- Run whether user is logged on or not
    - Do not store password
- Hidden: Yes
- Triggers: Daily 12:00, repeated every 1:00 for a duration of 1 day
- Action: Start a program
    - python
    - C:\Users\Path\to\folder\timing.py -l
    - Start in: C:\Users\Path\to\folder\
- Condition: Network - Start only if the following network connection is available: Any connection
- Stop if running more than an hour
- Force it to stop

I then use a desktop shortcut to start and stop the livetiming scheduled task. You will need to set the execution policy on Powershell for this to work, do so at your own risk. I recommend copying them to a new .ps1 file and setting the policy to RemoteSigned, but if you can't be bothered, set it to Bypass.
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
or
```
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

Then create two desktop shortcuts with targets to each script, one for start (enable) one for stop (disable)
```
powershell.exe -command "& 'C:\Users\path\to\scripts\ENABLE LIVE TIMING.ps1'"
```

Set the advanced setting on the shortcut to "Run as administrator" if you find they don't work. Our laptop has a blank password, so this is requried for our setup.

## Backup Event Files

I have also included a backup script that can be run as a scheduled task every 10 min. Useage is simillar to the Live Timing PowerShell. I created a folder under my synced HTML folder so that backups will be synced up to AWS.