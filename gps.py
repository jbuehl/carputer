import sys
import os
import time
import json

rootDir = "/root/data/"
logDir = rootDir+"gps/"
stateDir = rootDir
logFileName = "gps.csv"
stateFileName = "gps.json"
gpsDevice = "/dev/ttyUSB0"

nSats = 0
dateStamp = "000000"
timeStamp = "000000"
latitude = 0.0
latDir = ""
longitude = 0.0
longDir = ""
position = (0, "", 0, "")
altitude = 0.0
speed = 0.0
heading = 0.0
now = time.struct_time((2000, 1, 1, 0, 0, 0, 0, 0, 0))
lastTime = now
logFile = None
inFile = open(gpsDevice)

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
    return time.struct_time((year, month, day, hour, minute, second,0 ,0 ,0))

# set the system time
def setTime(now):
    print "Setting system time"
    os.system('date -s "'+time.asctime(now)+'"')

def parsePosition(latStr, latDir, longStr, longDir):
    return (str2float(latStr)/100, latDir, str2float(longStr)/100, longDir)

def parseAltitude(altStr):
    return str2float(altStr)*3.28084

def parseSpeed(speedStr):
    return (0.0 if str2float(speedStr) < 5 else str2float(speedStr)*1.15078)

def parseHeading(trackStr):
    return str2float(trackStr)
      
def str2float(value):
    try: return float(value)
    except: return 0.0
        
def str2int(value):
    try: return int(value)
    except: return 0

def formatTime(now):
    return time.strftime('%Y-%m-%d %H:%M:%S', now)

def formatPosition(position):
    return "%10.6f %s %10.6f %s" % (position[0], position[1], position[2], position[3])
        
def formatPrint(now, position, altitude, speed, heading, nSats):
     return "%s Position: %s  Altitude: %5d Speed: %3d Heading: %03d %d satellites" % \
            (formatTime(now), formatPosition(position), altitude, speed, heading, nSats)

def formatJson(now, position, altitude, speed, heading, nSats):
    return json.dumps({"Time": formatTime(now), "Pos": formatPosition(position), "Alt": altitude, "Speed": speed, "Hdg": heading, "Nsats": nSats})

while True:
    inMsg = inFile.readline()
    if logFile:
        logFile.write(inMsg)
        logFile.flush()
    gpsMsg = inMsg.rstrip("\n").split(",")
    if gpsMsg[0] == "$GPGGA":
        try:
            (timeStamp, latStr, latDir, longStr, longDir, quality, nSatsStr, dilution, altStr, altUnits, geoid, geoidUnits, whatever, chksum) = gpsMsg[1:15]
            now = curTime("", timeStamp, now)
            position = parsePosition(latStr, latDir, longStr, longDir)
            altitude = parseAltitude(altStr)
            nSats = str2int(nSatsStr)
        except:
            pass
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
            speed = parseSpeed(speedStr)
            heading = parseHeading(trackStr)
        except:
            pass
    elif gpsMsg[0] == "$GPVTG":
        pass
#    else:
#        if gpsMsg[0] != "":
#            print gpsMsg[0]
        
    if now != lastTime: # do this once per second
        lastTime = now
        if now[0] > 2000:   # don't write anything until valid time has been acquired
            if time.gmtime(time.time()).tm_year <= 2000:
                # set the system time
                setTime(now)
            if not logFile:
                logFile = open(logDir+time.strftime('%Y%m%d%H%M%S', now)+"-"+logFileName, "w")
            if logFile:
                if nSats > 0:
                    with open(stateDir+stateFileName, "w") as stateFile:
                        stateFile.write(formatJson(now, position, altitude, speed, heading, nSats))
    
