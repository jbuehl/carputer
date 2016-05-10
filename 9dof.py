from LSM9DS0 import IMU
import time
import json

rootDir = "/root/data/"
logDir = rootDir+"9dof/"
stateDir = rootDir
logFileName = "9dof.json"
stateFileName = stateDir+"9dof.json"

def writeState(stateFileName, state):        
    with open(stateFileName, "w") as stateFile:
        stateFile.write(json.dumps(state))

def writeLog(logFile, state):        
    logFile.write(json.dumps(state))
    logFile.flush()

logFile = open(logDir+time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))+"-"+logFileName, "w")

# Create IMU object
imu = IMU() # To select a specific I2C port, use IMU(n). Default is 1. 

# Initialize IMU
imu.initialize()

# Enable accel, mag, gyro, and temperature
imu.enable_accel()
imu.enable_mag()
imu.enable_gyro()
imu.enable_temp()

# Set range on accel, mag, and gyro

# Specify Options: "2G", "4G", "6G", "8G", "16G"
imu.accel_range("2G")       # leave blank for default of "2G" 

# Specify Options: "2GAUSS", "4GAUSS", "8GAUSS", "12GAUSS"
imu.mag_range("2GAUSS")     # leave blank for default of "2GAUSS"

# Specify Options: "245DPS", "500DPS", "2000DPS" 
imu.gyro_range("245DPS")    # leave blank for default of "245DPS"

# Loop and read accel, mag, and gyro
while(1):
    imu.read_accel()
    imu.read_mag()
    imu.read_gyro()
    imu.readTemp()

    # Print the results
    state = {"AccelX": imu.ax, "AccelY": imu.ay, "AccelZ": imu.az,
             "MagX": imu.mx, "MagY": imu.my, "MagZ": imu.mz,
             "GyroX": imu.gx, "GyroY": imu.gy, "GyroZ": imu.gz,
             "Temp": imu.temp}
    writeState(stateFileName, state)
    writeLog(logFile, state)

    # Sleep for 1 second
    time.sleep(1)
