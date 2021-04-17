# SCCNH Hillclimb LiveTiming

The goal of this Python script is to ingest live timing data and output files that can be hosted in an S3 bucket. This allows drivers and spectators to know how participants are doing throughout the day. This could be adapted to work with other systems, but our software uses a sqlite3 DB with a different file for each event in one directory.

## Installation

Python 3.6 or higher is required to be installed. The script is tested with python 3.9.2.
```
pip install -r requirements.txt
```
## Usage

Run the script interactively via command line

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
