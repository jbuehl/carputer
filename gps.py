import sys
import os
import time
import json
import timezonefinder
import pytz
import datetime

# configuration
debug = False
rootDir = "/root/data/"
logDir = rootDir+"gps/"
stateDir = rootDir
logFileBaseName = "gps.csv"
stateFileName = "gps.json"
gpsDevice = "/dev/ttyUSB0"
minSats = 0             # number of satellites required to start writing data
minSpeed = 5.0          # ignore speed if less than this value

# global variables
nSats = 0
#dateStamp = "000000"
#timeStamp = "000000"
latitude = 0.0
#latDir = ""
longitude = 0.0
#longDir = ""
position = (0, "", 0, "")
altitude = 0.0
speed = 0.0
heading = 0.0
now = time.struct_time((2000, 1, 1, 0, 0, 0, 0, 0, 0))
lastTime = now
timeZone = "America/Los_Angeles"
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
    print "Setting system time"
    os.system('date -s "'+time.asctime(now)+'"')

# parsing routines
def parsePosition(latStr, latDir, longStr, longDir):
    return (nmea2deg(str2float(latStr)), latDir, nmea2deg(str2float(longStr)), longDir)

def parseLatitude(latStr, latDir):
    latitude = nmea2deg(str2float(latStr))
    return (latitude if latDir == "N" else -latitude)

def parseLongitude(longStr, longDir):
    longitude = nmea2deg(str2float(longStr))
    return (longitude if latDir == "E" else -longitude)

def parseAltitude(altStr):
    return str2float(altStr)*3.28084

def parseSpeed(speedStr):
    return (0.0 if str2float(speedStr) < minSpeed else str2float(speedStr)*1.15078)

def parseHeading(trackStr):
    return str2float(trackStr)

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
def formatTime(now, tz):
    fmt = "%Y-%m-%d %H:%M:%S"
#    return datetime.datetime(*now[0:6], tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).strftime(fmt)
    return datetime.datetime(*now[0:6], tzinfo=pytz.utc).strftime(fmt)

def formatPosition(position):
    return "%10.6f %s %10.6f %s" % (position[0], position[1], position[2], position[3])
        
def formatPrint(now, position, altitude, speed, heading, nSats):
     return "%s Position: %s  Altitude: %5d Speed: %3d Heading: %03d %d satellites" % \
            (formatTime(now, timeZone), formatPosition(position), altitude, speed, heading, nSats)

#def formatJson(now, timeZone, position, altitude, speed, heading, nSats):
def formatState():
    return json.dumps({"Time": formatTime(now, timeZone), "TimeZone": timeZone, "Pos": formatPosition(position), "Lat": latitude, "Long": longitude, "Alt": altitude, "Speed": speed, "Hdg": heading, "Nsats": nSats})

if __name__ == "__main__":
    # open the serial port the gps device is connected to
    while not inFile:
        try:
            inFile = open(gpsDevice)
            if debug: print "opened gps device", gpsDevice
        except:
            if debug: print "waiting for gps device", gpsDevice
            time.sleep(1)

    timeZoneFinder = timezonefinder.TimezoneFinder()

    # read the gps data
    while True:
        inMsg = inFile.readline()

        # write to the log file if it is open which occurs after the time has been acquired
        if logFile:
            logFile.write(inMsg)
            logFile.flush()
            
        # parse the message
        gpsMsg = inMsg.rstrip("\n").split(",")
        if gpsMsg[0] == "$GPGGA":
            try:
                (timeStamp, latStr, latDir, longStr, longDir, quality, nSatsStr, dilution, altStr, altUnits, geoid, geoidUnits, whatever, chksum) = gpsMsg[1:15]
                now = curTime("", timeStamp, now)
                position = parsePosition(latStr, latDir, longStr, longDir)
                latitude = parseLatitude(latStr, latDir)
                longitude = parseLongitude(longStr, longDir)
                altitude = parseAltitude(altStr)
                nSats = str2int(nSatsStr)
            except:
                if debug: raise
        elif gpsMsg[0] == "$GPGSA":
            pass
        elif gpsMsg[0] == "$GPGSV":
            pass
        elif gpsMsg[0] == "$GPGLL":
            pass
        elif gpsMsg[0] == "$GPRMC":
            try:
                (timeStamp, status, latStr, latDir, longStr, longDir, speedStr, trackStr, dateStamp, magVar, chksum) = gpsMsg[1:12]
                now = curTime(dateStamp, timeStamp, now)
                position = parsePosition(latStr, latDir, longStr, longDir)
                latitude = parseLatitude(latStr, latDir)
                longitude = parseLongitude(longStr, longDir)
                speed = parseSpeed(speedStr)
                if speed > 0.0:   # retain last heading if stopped
                    heading = parseHeading(trackStr)
            except:
                if debug: raise
        elif gpsMsg[0] == "$GPVTG":
            pass
        else:
            if gpsMsg[0] != "":
                if debug: print "unknown gps message", gpsMsg[0]
            
        if now != lastTime: # do this once per second
            lastTime = now
            if now[0] > 2000:   # don't write anything until valid time has been acquired
                if first or (now[5] == 0): # set system time initially, then once per minute
                    timeZone = timeZoneFinder.timezone_at(lat=position[0] if position[1] == "N" else -position[0], lng=position[2] if position[3] == "E" else -position[2])
                    if debug: print "time zone", timeZone
                    # update the system time (always UTC)
                    if debug: print "setting time", now
                    setTime(now)
                    if debug: print formatPrint(now, position, altitude, speed, heading, nSats)
                    first = False
                if not logFile: # open a new log file if it hasn't happened yet
                    logFileName = logDir+time.strftime('%Y%m%d%H%M%S', now)+"-"+logFileBaseName
                    if debug: print "opening log file", logFileName
                    logFile = open(logFileName, "w")
                if logFile:
                    if nSats >= minSats:   # update the state file if we have acquired enough satellites
                        with open(stateDir+stateFileName, "w") as stateFile:
                            stateFile.write(formatState()) # formatJson(now, timeZone, position, altitude, speed, heading, nSats))
            else:
                if debug: print "waiting for date", now[0]
        
