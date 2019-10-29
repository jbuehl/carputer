
import serial
import json
import struct
import time

debugMsg = False
debugPids = False
debugData = False
debugDtc = False

diagDevice = "/dev/ttyUSB0"
diagBaud = 9600
rootDir = "/root/data/"
logDir = rootDir+"diags/"
stateDir = rootDir
logFileName = "diags.json"
stateFileName = stateDir+"diags.json"
waitTime = 0

diagState = {"Battery": 0.0,
             "Rpm": 0,
             "WaterTemp": 0,
             "Barometer": 0.0,
             "AirTemp": 0,
             "RunTime": 0,
             "NCodes": 0,
             "DiagCodes": "0",
             }

# send a request message to the specified port
def sendMsg(port, msg):
    if debugMsg: print(msg)
    port.write(bytes(msg+"\r", "utf-8"))

# read bytes from the specified port until a ">" prompt is received
# return the list of message lines that were received
def readMsgs(port):
    ch = ""
    msg = ""
    while ch != ">":
        ch = port.read(1).decode()
        msg += ch
    msgs = msg.split("\r")
    if debugMsg: print(msgs)
    return msgs

# return the message that was the response to a request
def readMsg(port):
    return readMsgs(port)[-3]

# return the OBD-II data for the specified mode and pid
def readObdData(port, mode, pid=None):
    request = "%02x" % mode
    if pid:
        request += "%02x" % pid
    if debugData: print("request: ", request)
    response = ""
    while response == "":
        sendMsg(diagPort, request)
        response = readMsg(port).replace(" ", "")
        if debugData: print("response:", response)
        if response in ["UNABLETOCONNECT", "CANERROR"]:
            print("retrying...")
            response = ""
            time.sleep(5)
    if ((mode == 1) and (pid == 1)) or (mode == 3):  # diag codes
        return response[4:]
    elif (mode == 9) and (pid == 2):  # VIN number
        return response[4:]
    else:                           # numeric response
        return int(response[4:], 16)

# return OBD-II data for the specified pid (modes 1, 2, 5, 9)
# def readPidData(port, mode, pid):
#     response = readObdData(port, mode, pid)
    # if len(response) == 2:
    #     fmt = "!B"
    # elif len(response) == 4:
    #     fmt = "!H"
    # elif len(response) == 8:
    #     fmt = "!L"
    # else:
    #     return response
    # return struct.unpack(fmt, response.decode("hex"))[0]

# return diagnostic data (mode 3)
def readDiagData(port):
    response = readObdData(port, 1, 0x01)
    # response = "82076500"
    checkEngine = int(response[0], 16)>>7 & 0x01
    nCodes = int(response[0], 16) & 0x7f
    if debugDtc: print("checkEngine:", checkEngine, "nCodes:", nCodes)
    dtcList = str(nCodes)+" "
    if nCodes > 0:
        response = readObdData(port, 3)
        # response = "00018003"
        for dtcPtr in range(0, len(response), 2):
            if response[dtcPtr:dtcPtr+2] != "\x00\x00":
                dtcList += parseDtc(response[dtcPtr:dtcPtr+2])+" "
    return (nCodes, dtcList[:-1])

# parse a DTC
#
# http://www.trouble-codes.com/
def parseDtc(msg):
    code = "PCBU"[ord(msg[0])>>6 & 0x03]
    code += hex(ord(msg[0])>>4 & 0x03)[-1]
    code += hex(ord(msg[0]) & 0x0f)[-1]
    code += hex(ord(msg[1])>>4 & 0x0f)[-1]
    code += hex(ord(msg[1]) & 0x0f)[-1]
    code = code.upper()
    if debugDtc: print("dtc:", code)
    return code

# clear diagnostic data (mode 4)
def clearDiagData(port):
    response = readObdData(port, 4)
    return response

# read the battery voltage from the ELM327
def readBattery(port):
    sendMsg(port, "atrv")       # battery voltage
    msg = readMsg(port)
    return float(msg.rstrip("V"))

# update the state file
def writeState(stateFileName, diagState):
    with open(stateFileName, "w") as diagFile:
        diagFile.write(json.dumps(diagState))

# write to the log file
def writeLog(logFile, diagState):
    logFile.write(json.dumps(diagState))
    logFile.flush()

# initialize
#
# https://cdn.sparkfun.com/assets/c/8/e/3/4/521fade6757b7fd2768b4574.pdf

logFile = logFile = open(logDir+time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))+"-"+logFileName, "w")
writeState(stateFileName, diagState)
diagPort = serial.Serial(diagDevice, baudrate=diagBaud)

# initialize the ELM327
sendMsg(diagPort, "atz")        # reset
msg = readMsg(diagPort)
sendMsg(diagPort, "ate0")       # echo off
msg = readMsg(diagPort)
sendMsg(diagPort, "atsp0")      # set protocol 0
msg = readMsg(diagPort)

# get supported PIDs
# https://en.wikipedia.org/wiki/OBD-II_PIDs

# 2008 Toyota Tacoma
#
# PID support query responses:
# 4100BF9FA893
# 41209105B11F
# 4140FADC2000
#
# Supported PID bits:
# BF9FA8939105B11FFADC2000
#
# Supported PIDs:
# 00,     02,     04, 05, 06, 07, 08, 09,         0c, 0d, 0e, 0f,
# 10, 11,     13,     15,             19,         1c,         1f,
# 20, 21,                         28,                     2e,
# 30, 31,     33, 34,             38,             3c, 3d, 3e, 3f,
# 40, 41, 42, 43, 44, 45,     47,     49, 4a,     4c, 4d, 4e,
#             53

pids = [readObdData(diagPort, 1, 0x00),
        readObdData(diagPort, 1, 0x20),
        readObdData(diagPort, 1, 0x40),
#        readObdData(diagPort, 1, 0x60),
#        readObdData(diagPort, 1, 0x80),
#        readObdData(diagPort, 1, 0xa0),
#        readObdData(diagPort, 1, 0xc0),
        ]
if debugPids: print("pids:", "%08x "*len(pids) % tuple(pids))

diagState["Vin"] = readObdData(diagPort, 9, 0x02)

# read vehicle data
running = True
while running:
    diagState["Battery"] = readBattery(diagPort)
    (nCodes, diagCodes) = readDiagData(diagPort)
    diagState["NCodes"] = nCodes
    diagState["DiagCodes"] = diagCodes
    diagState["WaterTemp"] = readObdData(diagPort, 1, 0x05) - 40
    diagState["Rpm"] = readObdData(diagPort, 1, 0x0c) / 4
    diagState["Speed"] = readObdData(diagPort, 1, 0x0d) * 0.621371
    diagState["IntakeTemp"] = readObdData(diagPort, 1, 0x0f) - 40
    diagState["RunTime"] = readObdData(diagPort, 1, 0x1f)
    diagState["Barometer"] = readObdData(diagPort, 1, 0x33) * 0.2953

    writeState(stateFileName, diagState)
    writeLog(logFile, diagState)
    time.sleep(waitTime)
    # running = False
