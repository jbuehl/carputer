# https://en.wikipedia.org/wiki/OBD-II_PIDs

import serial
import json
import struct
import time

debug = False
diagDevice = "/dev/ttyUSB1"
diagBaud = 9600
rootDir = "/root/data/"
logDir = rootDir+"diags/"
stateDir = rootDir
logFileName = "diags.json"
stateFileName = stateDir+"diags.json"
diagState = {"Battery": 0.0,
             "Rpm": 0, 
             "WaterTemp": 0,
             "AirTemp": 0}

def sendMsg(port, msg):
    if debug: print msg
    port.write(msg+"\r")
    
def readMsgs(port):
    ch = ""
    msg = ""
    while ch != ">":
        ch = port.read(1)
        msg += ch
    msgs = msg.split("\r")
    if debug: print msgs
    return msgs

def readMsg(port):
    return readMsgs(port)[-3]
    
def readData(port, mode, pid):
    response = ""
    while response == "":
        sendMsg(diagPort, "%02x%02x" % (mode, pid))
        response = readMsg(port).replace(" ", "")
        if debug: print response
        if response == "UNABLETOCONNECT":
            response = ""
            time.sleep(5)
    if len(response) == 6:
        fmt = "!BBB"
    elif len(response) == 8:
        fmt = "!BBH"
    elif len(response) == 12:
        fmt = "!BBL"
    else:
        return resp[4:]
    (respMode, respPid, respData) = struct.unpack(fmt, response.decode("hex"))
    return respData

def readBattery(port):
    sendMsg(port, "atrv")       # battery voltage
    msg = readMsg(port)
    return float(msg.rstrip("V"))

def writeState(stateFileName, diagState):        
    with open(stateFileName, "w") as diagFile:
        diagFile.write(json.dumps(diagState))

def writeLog(logFile, diagState):        
    logFile.write(json.dumps(diagState))
    logFile.flush()

# initialize
logFile = logFile = open(logDir+time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))+"-"+logFileName, "w")
writeState(stateFileName, diagState)
diagPort = serial.Serial(diagDevice, baudrate=diagBaud)
sendMsg(diagPort, "atz")        # reset
msg = readMsg(diagPort)
sendMsg(diagPort, "ate0")       # echo off
msg = readMsg(diagPort)
sendMsg(diagPort, "atsp0")      # set protocol 0
msg = readMsg(diagPort)

# get supported PIDs

# 4100BF9FA893
# 41209105B11F
# 4140FADC2000

# BF9FA8939105B11FFADC2000

# 00, 02, 04, 05, 06, 07, 08, 09, 0c, 0d, 0e, 0f, 10, 11, 13, 15, 19, 1c, 1f, 20
# 21, 28, 2e, 30, 31, 33, 34, 38, 3c, 3d, 3e, 3f, 40
# 41, 42, 43, 44, 45, 47, 49, 4a, 4c, 4d, 4e, 53

pids = [readData(diagPort, 1, 0x00),
        readData(diagPort, 1, 0x20),
        readData(diagPort, 1, 0x40),
#        readData(diagPort, 1, 0x60),
#        readData(diagPort, 1, 0x80),
#        readData(diagPort, 1, 0xa0),
#        readData(diagPort, 1, 0xc0)
        ]
#if debug: print "%08x "*7 % tuple(pids)

# read vehicle data
while True:
    diagState["WaterTemp"] = readData(diagPort, 1, 0x05) - 40
    diagState["Rpm"] = readData(diagPort, 1, 0x0c) / 4
    diagState["Speed"] = readData(diagPort, 1, 0x0d) * 0.621371
    diagState["IntakeTemp"] = readData(diagPort, 1, 0x0f) - 40
    diagState["RunTime"] = readData(diagPort, 1, 0x1f)
    diagState["Barometer"] = readData(diagPort, 1, 0x33) * 0.2953
    diagState["Battery"] = readBattery(diagPort)
    
    writeState(stateFileName, diagState)
    writeLog(logFile, diagState)
    time.sleep(1)
    

