import sys
import os
import time
import json
import pytz
import datetime
from elevation import *

# configuration
debug = False
haltOnError = False
rootDir = "/root/data/"
logDir = rootDir+"gps/"
stateDir = rootDir
logFileBaseName = "gps.csv"
stateFileName = "gps.json"
gpsDevices = ["/dev/serial0"]
gpsDevice = ""
minSats = 4             # number of satellites required to start writing data
minSpeed = 5.0          # ignore speed if less than this value

# state
nSats = 0
latitude = 0.0
longitude = 0.0
altitude = 0.0
gpsAltitude = 0.0
speed = 0.0
heading = 0.0
now = time.struct_time((2000, 1, 1, 0, 0, 0, 0, 0, 0))

# global variables
lastTime = now
logFile = None
inFile = None
first = True

# convert date/time stamps to current time
def curTime(dateStamp, timeStamp, now):
    if dateStamp != "":
        year = 2000+int(dateStamp[4:6])
        month = int(dateStamp[2:4])
        day = int(dateStamp[0:2])
    else:
        year = now[0]
        month = now[1]
        day = now[2]
    hour = int(timeStamp[0:2])
    minute = int(timeStamp[2:4])
    second = int(timeStamp[4:6])
    return time.struct_time((year, month, day, hour, minute, second, 0, 0, 0))

# set the system time
def setTime(now):
    if debug: print "Setting system time"
    os.system('date -s "'+time.asctime(now)+'"')

# data parsing routines
def parseLatitude(latStr, latDir):
    latitude = nmea2deg(str2float(latStr))
    return (latitude if latDir == "N" else -latitude)

def parseLongitude(longStr, longDir):
    longitude = nmea2deg(str2float(longStr))
    return (longitude if longDir == "E" else -longitude)

def parseAltitude(altStr):
    return str2float(altStr)*3.28084

def parseSpeed(speedStr):
    return (0.0 if str2float(speedStr) < minSpeed else str2float(speedStr)*1.15078)

def parseHeading(trackStr):
    return str2float(trackStr)

# message parsing routines
def parseGGA(gpsMsg):
    global now, nSats, latitude, longitude, altitude, gpsAltitude
    try:
        (timeStamp, latStr, latDir, longStr, longDir, quality, nSatsStr, dilution, altStr, altUnits, geoid, geoidUnits, whatever) = gpsMsg[1:14]
        if timeStamp != "": now = curTime("", timeStamp, now)
        nSats = str2int(nSatsStr)
        if nSats > minSats: # only store valid data
            latitude = parseLatitude(latStr, latDir)
            longitude = parseLongitude(longStr, longDir)
            gpsAltitude = parseAltitude(altStr)
            altitude = getElevation(latitude, longitude, gpsAltitude)
    except:
        if debug:
            print gpsMsg
            if haltOnError: raise

def parseRMC(gpsMsg):
    global now, speed, heading
    try:
        (timeStamp, status, latStr, latDir, longStr, longDir, speedStr, trackStr, dateStamp, magVar) = gpsMsg[1:11]
        if timeStamp != "": now = curTime(dateStamp, timeStamp, now)
        if nSats > minSats:# only store valid data
            speed = parseSpeed(speedStr)
            if speed > 0.0:   # retain last heading if stopped
                heading = parseHeading(trackStr)
    except:
        if debug:
            print gpsMsg
            if haltOnError: raise

def parseZDA(gpsMsg):
    global now
    try:
        (timeStamp, day, month, year, tzHour, tzMinutes) = gpsMsg[1:7]
        if timeStamp != "": now = curTime(day+month+year[2:], timeStamp, now)
    except:
        if debug:
            print gpsMsg
            if haltOnError: raise

# convert a NMEA location value ddmm.mmmm to degrees dd.dddddd
def nmea2deg(value):
    deg = int(value/100)
    return deg + (value - deg*100)/60

def str2float(value):
    try: return float(value)
    except: return 0.0

def str2int(value):
    try: return int(value)
    except: return 0

# formatting routines
def formatTime(now):
    fmt = "%Y-%m-%d %H:%M:%S"
    return datetime.datetime(*now[0:6], tzinfo=pytz.utc).strftime(fmt)

def formatPrint():
     return "%s Lat:%7.3f  Long:%7.3f  Alt:%5d GPSAlt:%5d Speed:%3d Hdg:%03d Nsats:%d" % \
            (formatTime(now), latitude, longitude, altitude, gpsAltitude, speed, heading, nSats)

# state routines
def parseState(state):
    global latitude, longitude, altitude, speed, heading
    try:
        latitude = state["Lat"]
        longitude = state["Long"]
        altitude = state["Alt"]
        gpsAltitude = state["GPSAlt"]
        speed = state["Speed"]
        heading = state["Hdg"]
    except:
        if haltOnError: raise

def readState():
    if debug: print "reading state from", stateDir+stateFileName
    try:
        with open(stateDir+stateFileName) as stateFile:
            parseState(json.load(stateFile))
    except:
        if haltOnError: raise
    if debug: print formatPrint()

def formatState():
    return json.dumps({"Time": formatTime(now),
                       "Lat": latitude, "Long": longitude, "Alt": altitude, "GPSAlt": gpsAltitude,
                       "Speed": speed, "Hdg": heading, "Nsats": nSats,
                       "GPSDevice": gpsDevice})

def writeState():
    if debug: print "writing state to", stateDir+stateFileName
    with open(stateDir+stateFileName, "w") as stateFile:
        stateFile.write(formatState())

if __name__ == "__main__":
    # open the serial port the gps device is connected to
    while not inFile:
        for device in gpsDevices:
            try:
                inFile = open(device)
                if debug: print "opened gps device", device
                gpsDevice = device[5:]
                break
            except IOError:
                if debug: print "error opening gps device", device
        if not inFile:
            if debug: print "waiting for gps device"
            time.sleep(1)

    # read the last known state
    readState()

    # read the gps data
    while True:
        inMsg = inFile.readline()
        if False:
            if len(inMsg) > 1:
                print len(inMsg), inMsg,

        # write to the log file if it is open which occurs after the time has been acquired
        if logFile:
            logFile.write(inMsg)
            logFile.flush()

        # parse the message
        (gpsMsg, ckSum) = inMsg.rstrip("\r\n").split("*")
        gpsMsg = gpsMsg.split(",")
        if gpsMsg[0] == "$GPGGA":
            parseGGA(gpsMsg)
        elif gpsMsg[0] == "$GPGSA":
            pass
        elif gpsMsg[0] == "$GPGSV":
            pass
        elif gpsMsg[0] == "$GPGLL":
            pass
        elif gpsMsg[0] == "$GPRMC":
            parseRMC(gpsMsg)
        elif gpsMsg[0] == "$GPVTG":
            pass
        elif gpsMsg[0] == "$GPZDA":
            parseZDA(gpsMsg)
        else:
            if gpsMsg[0] != "":
                if debug: print "unknown gps message", gpsMsg[0]

        if now != lastTime: # do this once per second
            if debug: print formatPrint()
            lastTime = now
            if now[0] > 2000:   # don't write anything until valid time has been acquired
                if first or (now[5] == 0): # set system time initially, then once per minute
                    # update the system time (always UTC)
                    setTime(now)
                    first = False
                if not logFile: # open a new log file if it hasn't happened yet
                    logFileName = logDir+time.strftime('%Y%m%d%H%M%S', now)+"-"+logFileBaseName
                    if debug: print "opening log file", logFileName
                    logFile = open(logFileName, "w")
                if logFile:
                    # if (nSats >= minSats) and (latitude != 0.0):   # update the state file if we have acquired enough satellites
                        writeState()
            else:
                if debug: print "waiting for date", now[0]
