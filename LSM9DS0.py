import smbus
import numpy as np

# Class for accel/mag/temp configuration and registers
class XM:
    ADDRESS = 0x1D
    WHO_AM_I = 0x0F    # r
    WHO_AM_I_OK = 0x49  #r
    OUT_TEMP_L_XM = 0x05 # r
    OUT_TEMP_H_XM = 0x06 # r
    STATUS_REG_M = 0x07 # r
    OUT_X_L_M = 0x08 # r
    OUT_X_H_M = 0x09 # r
    OUT_Y_L_M = 0x0A # r
    OUT_Y_H_M = 0x0B # r
    OUT_Z_L_M = 0x0C # r
    OUT_Z_H_M = 0x0D # r
    INT_CTRL_REG_M = 0x12 # rw
    INT_SRC_REG_M = 0x13 # r
    INT_THS_L_M = 0x14 # rw
    INT_THS_H_M = 0x15 # rw
    OFFSET_X_L_M = 0x16 # rw
    OFFSET_X_H_M = 0x17 # rw
    OFFSET_Y_L_M = 0x18 # rw
    OFFSET_Y_H_M = 0x19 # rw
    OFFSET_Z_L_M = 0x1A # rw
    OFFSET_Z_H_M = 0x1B # rw
    REFERENCE_X = 0x1C # rw
    REFERENCE_Y = 0x1D # rw
    REFERENCE_Z = 0x1E # rw
    CTRL_REG0_XM = 0x1F # rw
    CTRL_REG1_XM = 0x20 # rw
    CTRL_REG2_XM = 0x21 # rw
    CTRL_REG3_XM = 0x22 # rw
    CTRL_REG4_XM = 0x23 # rw
    CTRL_REG5_XM = 0x24 # rw
    CTRL_REG6_XM = 0x25 # rw
    CTRL_REG7_XM = 0x26 # rw
    STATUS_REG_A = 0x27 # r
    OUT_X_L_A = 0x28 # r
    OUT_X_H_A = 0x29 # r
    OUT_Y_L_A = 0x2A # r
    OUT_Y_H_A = 0x2B # r
    OUT_Z_L_A = 0x2C # r
    OUT_Z_H_A = 0x2D # r
    FIFO_CTRL_REG = 0x2E # rw
    FIFO_SRC_REG = 0x2F # r
    INT_GEN_1_REG = 0x30 # rw
    INT_GEN_1_SRC = 0x31 # r
    INT_GEN_1_THS = 0x32 # rw
    INT_GEN_1_DURATION = 0x33 # rw
    INT_GEN_2_REG = 0x34 # rw
    INT_GEN_2_SRC = 0x35 # r
    INT_GEN_2_THS = 0x36 # rw
    INT_GEN_2_DURATION =  0x37 # rw
    CLICK_CFG = 0x38 # rw
    CLICK_SRC = 0x39 # r
    CLICK_THS = 0x3A # rw
    TIME_LIMIT = 0x3B # rw
    TIME_LATENCY = 0x3C # rw
    TIME_WINDOW = 0x3D # rw
    ACT_THS = 0x3E # rw
    ACT_DUR = 0x3F # rw
    RANGE_M = {'2GAUSS': (0b00 << 5), '4GAUSS': (0b01 << 5), '8GAUSS': (0b10 << 5), '12GAUSS': (0b11 << 5)}
    RANGE_A = {'2G':(0b000 << 3),'4G':(0b001 << 3),'6G':(0b010 << 3),'8G':(0b011 << 3),'16G':(0b100 << 3)}
    CAL_M = {'2GAUSS': (2.0/32768.0), '4GAUSS': (4.0/32768.0), '8GAUSS': (8.0/32768.0), '12GAUSS': (12.0/32768.0)}
    CAL_A = {'2G': (2.0/32768.0),'4G': (4.0/32768.0),'6G':(6.0/32768.0),'8G':(8.0/32768.0),'16G':(16.0/32768.0)}
    CAL_TEMP = 1.0/8.0


# Class for gyro configuration and registers
class GYRO:
    ADDRESS = 0x6b
    WHO_AM_I = 0x0F # r
    WHO_AM_I_OK = 0xD4 #r
    CTRL_REG1_G = 0x20 # rw
    CTRL_REG2_G = 0x21 # rw
    CTRL_REG3_G = 0x22 # rw
    CTRL_REG4_G = 0x23 # rw
    CTRL_REG5_G = 0x24 # rw
    REFERENCE_G = 0x25 # rw
    STATUS_REG_G = 0x27 # r
    OUT_X_L_G = 0x28 # r
    OUT_X_H_G = 0x29 # r
    OUT_Y_L_G = 0x2A # r
    OUT_Y_H_G = 0x2B # r
    OUT_Z_L_G = 0x2C # r
    OUT_Z_H_G = 0x2D # r
    FIFO_CTRL_REG_G = 0x2E # rw
    FIFO_SRC_REG_G = 0x2F # r
    INT1_CFG_G = 0x30 # rw
    INT1_SRC_G = 0x31 # r
    INT1_TSH_XH_G = 0x32 # rw
    INT1_TSH_XL_G = 0x33 # rw
    INT1_TSH_YH_G = 0x34 # rw
    INT1_TSH_YL_G = 0x35 # rw
    INT1_TSH_ZH_G = 0x36 # rw
    INT1_TSH_ZL_G = 0x37 # rw
    INT1_DURATION_G = 0x38 # rw
    RANGE_G = {'245DPS': (0b00 << 4), '500DPS': (0b01 << 4), '2000DPS': (0b10 << 4)}
    CAL_G = {'245DPS': (245.0/32768.0), '500DPS': (500.0/32768.0), '2000DPS': (2000.0/32768.0)}

""" Function to parse the data bytes
Inputs:
    b: byte array of 2-axis data, odd = high byte, even = low byte
Outputs:
    x, y, z: signed 16-bit integer of x, y, and z values
"""
def parsedata(b, cal):
    x = np.int16(b[0] | (b[1] << 8))*cal
    y = np.int16(b[2] | (b[3] << 8))*cal
    z = np.int16(b[4] | (b[5] << 8))*cal
    return x, y, z


""" Function to read the uncalibrated data from a 3-axis sensor
Inputs:
    x: I2C object from mraa
    address: address of sensor - accel/mag or gyro
    reg: register to read for specific data and config
Outputs:
    x, y, z: signed 16-bit integer of x, y, and z values
"""
def read3axis(x, address, reg, cal):
    data = x.read_i2c_block_data(address, 0x80 | reg, 6)
    x, y, z = parsedata(data, cal)
    return x, y, z 


# IMU Class 
class IMU:

    # Mag and Gyro Configs loaded
    XM = XM
    G = GYRO

    # Default mag, gyro, and accel ranges loaded
    selected_a_range = '2G'
    selected_m_range = '2GAUSS'
    selected_g_range = '245DPS'

    # Initialize I2C port for 9-axis IMU
    def __init__(self, I2CPort=1):
        self.x = smbus.SMBus(I2CPort)

    # Initialize - checking gyro and mag are properly connected
    def initialize(self):
        resp = self.x.read_byte_data(self.G.ADDRESS, self.G.WHO_AM_I)
        if resp == self.G.WHO_AM_I_OK:
            print "Gyro init success!"
        else:
            print "Gyro init failed"
        # Check accel/mag - expect back 0x49 = 73L if connected to 9dof breakout
        resp = self.x.read_byte_data(self.XM.ADDRESS, self.XM.WHO_AM_I)
        if resp == self.XM.WHO_AM_I_OK:
            print "Accel/Mag init success!"
        else:
            print "Accel/Mag init failed"

    # Enables the accelerometer, 100 Hz continuous in X, Y, and Z
    def enable_accel(self):
        self.x.write_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG1_XM, 0x67)  # 100 Hz, XYZ
        self.x.write_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG5_XM, 0xF0)

    # Enables the gyro in normal mode on all axes
    def enable_gyro(self):
        self.x.write_byte_data(self.G.ADDRESS, self.G.CTRL_REG1_G, 0x0F) # normal mode, all axes

    # Enables the mag continuously on all axes
    def enable_mag(self):
        self.x.write_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG7_XM, 0x00)  # continuous

    # Enables temperature measurement at the same frequency as mag  
    def enable_temp(self):
        rate = self.x.read_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG5_XM)  
        self.x.write_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG5_XM, (rate | (1<<7)))  

    # Sets the range on the accelerometer, default is +/- 2Gs
    def accel_range(self,AR="2G"):
        try:
            Arange = self.XM.RANGE_A[AR]
            accelReg = self.x.read_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG2_XM)
            accelReg |= Arange
            self.x.write_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG2_XM, accelReg)
            self.selected_a_range = AR
        except(KeyError):
            print("Invalid range. Valid range keys are '2G', '4G', '6G', '8G', or '16G'")

    # Sets the range on the mag - default is +/- 2 Gauss
    def mag_range(self,MR="2GAUSS"):
        try:
            Mrange = self.XM.RANGE_M[MR]
            magReg = self.x.read_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG6_XM)
            magReg &= ~(0b01100000)
            magReg |= Mrange
            self.x.write_byte_data(self.XM.ADDRESS, self.XM.CTRL_REG6_XM, magReg)
            self.selected_m_range = MR
        except(KeyError):
            print("Invalid range. Valid range keys are '2GAUSS', '4GAUSS', '8GAUSS', or '12GAUSS'")

    # Sets the range on the gyro - default is +/- 245 degrees per second
    def gyro_range(self,GR="245DPS"):
        try:
            Grange = self.G.RANGE_G[GR]
            gyroReg = self.x.read_byte_data(self.XM.ADDRESS, self.G.CTRL_REG4_G)
            gyroReg &= ~(0b00110000)
            gyroReg |= Grange;
            self.x.write_byte_data(self.G.ADDRESS, self.G.CTRL_REG4_G, gyroReg)
            self.selected_g_range = GR
        except(KeyError):
            print("Invalid range. Valid range keys are '245DPS', '500DPS', or '2000DPS'")

    # Reads and calibrates the accelerometer values into Gs
    def read_accel(self):
        cal = self.XM.CAL_A[self.selected_a_range]
        self.ax, self.ay, self.az = read3axis(self.x, self.XM.ADDRESS, self.XM.OUT_X_L_A, cal)
    
    # Reads and calibrates the mag values into Gauss
    def read_mag(self):
        cal = self.XM.CAL_M[self.selected_m_range]
        self.mx, self.my, self.mz = read3axis(self.x, self.XM.ADDRESS, self.XM.OUT_X_L_M, cal) 
    
    # Reads and calibrates the gyro values into degrees per second
    def read_gyro(self):
        cal = self.G.CAL_G[self.selected_g_range]
        self.gx, self.gy, self.gz = read3axis(self.x, self.G.ADDRESS, self.G.OUT_X_L_G, cal)  
    
    # Reads and calibrates the temperature in degrees C
    def readTemp(self):
        tempdata = self.x.read_i2c_block_data(self.XM.ADDRESS, 0x80 | self.XM.OUT_TEMP_L_XM, 2)
        temp = np.int16(((tempdata[1] >> 4) << 8) | tempdata[0])
        self.temp = temp * self.XM.CAL_TEMP


