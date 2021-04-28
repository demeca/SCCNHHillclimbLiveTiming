"""SCCNH Live Hillclimb Timing

Usage:
    timing.py
    timing.py [options]

Options:
    -h, --help              Show this screen
    --version               Show version
    -d, --dir               Enter an event directory
    -e INT, --event INT     Enter an event number
    -f, --force             Force an update
    -l, --latest            Use last edited event file as input
"""

import os
import glob
import sqlite3
from config import config
from collections import defaultdict
from datetime import date, timedelta, time, datetime
from docopt import docopt
from dateutil import parser

# Get info from enviroment

fileLocation = config.get("eventPath")
print("Event File Location Set:", fileLocation)
outDir = config.get("outDir")
print("Output Directory Set:", outDir)
# Get file list from directory
fileList = os.listdir(fileLocation)
# Events have predictable filenames in our software
# Pull out the event numbers without the extensions or other files
eventList = [x[:8] for x in fileList if x[0]=='E']
# Keep a list of unique events
eventList = list(set(eventList))
# Sort events
eventList.sort()

#get header and footer
headFile = open(f'{outDir}/basehtmlHeader.html', 'r')
htmlHeader = headFile.read()
headFile.close()
footFile = open(f'{outDir}/basehtmlfooter.html', 'r')
htmlFooter = footFile.read()
footFile.close()

# Ask for event in that location
def pick_event(eventList, pick):
    if not pick:
        print("Choose and event to use:")
        for i, e in enumerate(eventList):
            print(f"{i+1}. {e}")
        pick = input("Enter number: ")
    try:
        if 0 < int(pick) <= len(eventList):
            return eventList[int(pick) - 1]
    except Exception as ex:
        print("Entry not valid.")
    return None

# Open SQL
def get_event_info(eventSQLFile):
    # Open DB read-only
    sqlPath = 'file:' + eventSQLFile + '?mode=ro'
    con = sqlite3.connect(sqlPath, uri=True)
    if con:
        print("Event Connected")
    cur = con.cursor()
    eventInfo = {}
    for row in cur.execute("""SELECT C_PARAM, C_VALUE FROM "main"."TPARAMETERS" WHERE "C_PARAM" = 'LOCATION' OR "C_PARAM" = 'DATE' OR "C_PARAM" = 'TITLE1' OR "C_PARAM" = 'TITLE2' OR "C_PARAM" = 'TIMING_BY' OR "C_PARAM" = 'TIME_ACCURACY'"""):
        eventInfo[row[0]] = row[1]
    con.close()
    if not eventInfo:
        print("Event Info Not Found")
    return eventInfo

# Get Event Date
# Event date is stored as days since 1900
# Day 1 is 1/1/1900
def getDate(days):
    start = date(1900, 1, 1)
    delta = timedelta(int(days) - 2)
    offsetDate = start + delta
    return offsetDate

# Get Competitors
def get_competitors_list(eventSQLFile):
    # Open DB read-only
    sqlPath = 'file:' + eventSQLFile + '?mode=ro'
    con = sqlite3.connect(sqlPath, uri=True)
    cur = con.cursor()
    competitors = {}
    for row in cur.execute("""SELECT "C_NUM", "C_TRANSPONDER1", "C_LAST_NAME", "C_FIRST_NAME", "C_CATEGORY", "C_SERIE", "C_I27" FROM "main"."TCOMPETITORS"; """):
        entry = {}
        entry['NUM'] = row[0]
        entry['FULLNUM'] = row[1]
        entry['LAST_NAME'] = row[2]
        entry['FIRST_NAME'] = row[3]
        entry['CLASS'] = row[4]
        entry['CAR'] = row[5]
        entry['X_CLASS'] = row[6]
        competitors[row[0]] = entry
    con.close()
    return competitors

# Get Heat List and Times
def get_heatlist_and_times(eventSQLFile):
    # Open DB read-only
    sqlPath = 'file:' + eventSQLFile + '?mode=ro'
    con = sqlite3.connect(sqlPath, uri=True)
    cur = con.cursor()
    heats = []
    for row in cur.execute("""SELECT name FROM "main".sqlite_master WHERE type = 'table' AND name LIKE 'TTIMEINFOS_HEAT%';"""):
        heats.append([int(row[0][15:]),row[0]])
    heats.sort()
    heatRuns = []
    carRuns = defaultdict(list)
    statusCodes = {0: 'OK', 1: 'DNS', 2:'DNF'}
    for heatNum, heatTable in heats:
        runs = []
        for row in cur.execute(f'SELECT "C_NUM", "C_TIME", "C_PENALTY", "C_INTER1", "C_STATUS"  FROM "main"."{heatTable}";'):
            run = {}
            time = timedelta(seconds=row[1]/1000)
            min, seconds = divmod(time.seconds, 60)
            seconds += time.microseconds / 1e6
            stringTime = f"{min:02d}:{seconds:06.3f}"
    #print("Heat", heatNum, "| Car", row[0], "| TIME:", min, ":", seconds, "| raw", row[1]/1000)
            run['HEAT'] = heatNum
            run['NUM'] = row[0]
            run['TIME'] = time
            run['STRTIME'] = stringTime
            run['PENALTY'] = row[2]
            run['SPLIT'] = row[3]
            run['STATUS'] = statusCodes.get(int(row[4]), 'ERR')
            carRuns[row[0]].append(run)
            runs.append(run)
        heatRuns.append([heatNum, runs])
    con.close()
    return heatRuns, carRuns

# Create homepage with overall ranking
def create_homepage(entries, eventInfo):
    heatList = f"""
        <h1>SCCNH Livetiming</h1><h4>**ALL TIMES UNOFFICAL**</h4>
        <h1>Event: {eventInfo['TITLE1']}</h1>
        <h2>{eventInfo['TITLE2']}</h2>
        <h4>Location: {eventInfo['LOCATION']}</h4><h4> Date: {eventInfo['DATE']}</h4>
        <p>Updated: {datetime.now().strftime("%B %d, %Y %I:%M%p")}</p>
        """
    heatFiles = glob.glob(f'{outDir}/heats/Heat*.html')
    heats = [[int(os.path.basename(f)[:-5][4:]), "heats/" + os.path.basename(f)] for f in heatFiles]
    heats.sort(key=lambda x: x[0])
    entries.sort(key=lambda x: x.get('BEST', timedelta(seconds=999999999999)))
    heatList += "<br/ ><h2>Runs by Heat</h2>"
    for heat in heats:
        heatList += f"<a class='btn btn-primary' href={heat[1]}>Heat {heat[0]}</a> "

    heatList += "<br/ ><br /><h2>All Runs by Class</h2>"

    classFiles = glob.glob(f'{outDir}/class/C-*.html')
    cClass = [[os.path.basename(f)[:-5][2:], "class/" + os.path.basename(f)] for f in classFiles]
    cClass.sort(key=lambda x: x[0])
    for c in cClass:
        if c[0] == "":
            c[0] = "No Class"
        heatList += f"<a class='btn btn-primary' href={c[1]}>{c[0]}</a> "
    
    heatList += f"""
        <br />
        <br />
        <h2>Best Runs</h2>
        <table class="table table-striped table-hover">
            <thead>
            <tr>
                <th scope="col">Num</th>
                <th scope="col">Name</th>
                <th scope="col">Class</th>
                <th scope="col">Car</th>
                <th scope="col">Best</th>
            </tr>
            </thead>
            <tbody>"""
    for entry in entries:
        heatList += f"""
            <tr>
                <td>{entry.get('FULLNUM')}</td>
                <td>{entry.get('FIRST_NAME')} {entry.get('LAST_NAME')}</td>
                <td>{entry.get('CLASS')}</td>
                <td>{entry.get('CAR')}</td>
                <td>{entry.get('BESTSTR')}</td>
            </tr>"""
    
    heatList +="</tbody></table>"
    #output file
    outFile = open(f"{outDir}/index.htm", "w")
    outFile.write(htmlHeader)
    outFile.write(heatList)
    outFile.write(htmlFooter)
    outFile.close()


# Create by runset html
def create_heat_html_files(heatNum, runs, entries):
    runTable = f"""
    <h2>Heat {heatNum} Runs</h2>
    <p>Go to the class page to see all your runs and to see
    your times ranked against others in your class.
    The results below are ordered by car number.
    </p>
    <table class="table table-striped table-hover">
        <thead>
        <tr>
            <th scope="col">Num</th>
            <th scope="col">Name</th>
            <th scope="col">Car</th>
            <th scope="col">Class</th>
            <th scope="col">Time (MM:SS.FFF)</th>
            <th scope="col">Penalty</th>
            <th scope="col">Time Status</th>
        </tr>
        </thead>
        <tbody>
    """
    for run in runs:
        entry = None
        fullNum = None
        entry = entries.get(run.get('NUM'))
        if entry:
            fullNum = entry.get('FULLNUM')
        if fullNum:
            runTable += f"""
            <tr>
                <td>{fullNum}</td>
                <td>{entries.get(run.get('NUM')).get('FIRST_NAME')} {entries.get(run.get('NUM')).get('LAST_NAME')}</td>
                <td>{entries[run.get('NUM')]['CAR']}</td>
                <td>{entries[run.get('NUM')]['CLASS']}</td>"""
        else:
            runTable += f"<td>{run.get('NUM')}</td><td></td><td></td><td></td>"
        runTable += f"""
                <td>{run.get('STRTIME')}</td>
                <td>{run.get('PENALTY')}</td>
                <td>{run.get('STATUS')}</td>
            </tr>"""
    runTable += "</tbody></table>"
    #output file
    outFile = open(f"{outDir}/heats/Heat{heatNum}.html", "w")
    outFile.write(htmlHeader)
    outFile.write(runTable)
    outFile.write(htmlFooter)
    outFile.close()

def clean_heat_folder():
    files = glob.glob(f'{outDir}/heats/Heat*.html')
    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error Deleting {f}: {e.strerror}")

def clean_class_folder():
    files = glob.glob(f'{outDir}/class/*.html')
    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error Deleting {f}: {e.strerror}")

# Create by class html
def create_class_html_files(classRuns, entries):
    for c, runs in classRuns.items():
        outFile = open(f"{outDir}/class/C-{c}.html", "w")
        outFile.write(htmlHeader)
        carRuns = """<table class="table table-striped table-hover">
                        <thead>
                            <th>Pos</th>
                            <th>Num</th>
                            <th>Name</th>
                            <th>Car</th>
                            <th colspan=5>Runs</th>
                            <th>Best Run</th>
                        <thead>
                        <tbody>"""
        
        runs.sort(key=lambda x: x[2])
        placeCount = 0
        for run in runs:
            placeCount += 1
            carRuns += f"""
                <tr>
                    <td>{placeCount}</td>
                    <td>{entries[run[0]].get("FULLNUM")}</td>
                    <td>{entries[run[0]].get('FIRST_NAME')} {entries[run[0]].get('LAST_NAME')}</td>
                    <td>{entries[run[0]].get('CAR')}</td>
                    <td colspan=5>
                    <table class="table"><tr>"""
            count = 0
            for h, t in run[1].items():
                if count % 5 == 0:
                    carRuns += "</tr><tr>"
                if t[0] == run[2]:
                    carRuns += f"<td><b>{h}: {t[0]}</b>"
                else:
                    carRuns += f"<td>{h}: {t[0]}"
                if t[1] != 'OK':
                    carRuns += "/" + t[1]
                carRuns += "</td>"
                count += 1
            carRuns += f"""</tr></table></td>
                    <td><b>{run[2]}</b></td>
                </tr>
            """
        carRuns += "</tbody></table>"
        outFile.write(carRuns)
        outFile.write(htmlFooter)
        outFile.close()


# Update AWS Bucket using the AWS CLI
def trigger_s3_upload():
    cmd = config["AWSCommand"]
    print("Running:", cmd)
    result = os.system(cmd)
    print(result)
    if result == 0:
        print("Upload Success")
    else:
        print("Upload Error")

def check_for_update(event):
    try:
        timeFile = open("lastupdate.txt", "r")
        contents = timeFile.read()
        timeFile.close()
    except FileNotFoundError:
        contents = "None:00000"
    try:
        eventFile, time = contents.split(":")
    except ValueError:
        eventFile = "None"
        time = 000000
    if event != eventFile:
        timeFile = open("lastupdate.txt", "w+")
        timeFile.write(event + ":" + str(os.path.getmtime(fileLocation + "/" + event + "Ex.scdb")))
        timeFile.close()
        return True
    
    if os.path.getmtime(fileLocation + "/" + event + "Ex.scdb") > float(time):
        timeFile = open("lastupdate.txt", "w+")
        timeFile.write(event + ":" + str(os.path.getmtime(fileLocation + "/" + event + "Ex.scdb")))
        timeFile.close()
        return True

    return False


def get_latest_file():

    list_of_files = glob.glob(fileLocation + "/*Ex.scdb")
    latest_file = max(list_of_files, key=os.path.getmtime)
    return os.path.basename(latest_file)[:8]
    

if __name__ == '__main__':
    opts = docopt(__doc__, version="1.0")
    pick = None
    event = None
    if config.get("eventNumber", None):
        pick = config.get("eventNumber")
    if opts.get('--event'):
        pick = opts.get('--event')
    if opts.get('--latest'):
        event = get_latest_file()
    if not event:
        event = pick_event(eventList, pick)
    if event:
        print("Event Found")
        if check_for_update(event) or opts.get('--force'):
            eventFile = fileLocation + "/" + event + ".scdb"
            timesFile = fileLocation + "/" + event + "Ex.scdb"
            eventInfo = get_event_info(eventFile)
            eventInfo['DATE'] = getDate(eventInfo.get('DATE'))
            entries = get_competitors_list(eventFile)
            #print(eventInfo)
            #print(entries)
            heatRuns, carRuns = get_heatlist_and_times(timesFile)
            clean_heat_folder()
            clean_class_folder()
            for heat, runset in heatRuns:
                if len(runset):
                    #print(runset)
                    create_heat_html_files(heat, runset, entries)
            
            byClass = defaultdict(list)
            runsByClass = defaultdict(list)

            for car in entries:
                allRuns = carRuns.get(car)
                if allRuns:
                    #allRuns.sort(key=lambda x: x.get("TIME"))
                    min = None
                    justTimes = [x.get("TIME") for x in allRuns]
                    for time in justTimes:
                        if time and (min is None or time < min):
                            min = time
                    entries[car]['BEST'] = min
                    minute, seconds = divmod(min.seconds, 60)
                    seconds += min.microseconds / 1e6
                    entries[car]['BESTSTR'] = f"{minute:02d}:{seconds:06.3f}"
                    
                    cClass = entries[car]['CLASS']
                    heatTimes = {}
                    for run in allRuns:
                        heatTimes[run["HEAT"]] =  [run["STRTIME"], run["STATUS"], run["PENALTY"]]
                    runsByClass[cClass].append([car, heatTimes, entries[car]['BESTSTR']])
                    #print(allRuns)
                    
            create_class_html_files(runsByClass, entries)
            create_homepage(list(entries.values()), eventInfo)
            print("Data processed")
            trigger_s3_upload()
