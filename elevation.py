elevDir = "/root/elevation/"    # directory containing SRTM files
resolution = 3600   # resolution of the data points with a file
feetPerMeter = 3.28084
curFileName = ""
elevData = ""

import struct

# return the elevation in feet of the surface at the specified coordinates
# using the 1" North American SRTM database
# https://dds.cr.usgs.gov/srtm/version2_1/SRTM1/
# http://fileformats.archiveteam.org/wiki/HGT
def getElevation(lat, long, gpsElev=0.0):
    global curFileName, elevData
    # determine the SRTM file name based on the lat/long
    if lat >= 0:
        elevFileName = "N"+str(int(lat))
        row = int((1.0 - lat + int(lat)) * resolution)
    else:   # not tested
        elevFileName = "S"+str(int(-lat)+1)
        row = int((lat - int(lat)) * resolution)
    if long >= 0:   # not tested
        elevFileName += "E"+str(int(long))
        col = int((long - int(long)) * resolution)
    else:
        elevFileName += "W"+str(int(-long)+1)
        col = int((1.0 + long - int(long)) * resolution)
    # read the data from the file if it hasn't already
    if elevFileName != curFileName:
        try:
            with open(elevDir+elevFileName+".hgt") as elevFile:
                elevData = elevFile.read()
            curFileName = elevFileName
        except IOError: # data not available - return the gps elevation
            return gpsElev
    # compute the offset into the data for the location
    offset = row * 2 * (resolution + 1) + 2 * col
    elev = struct.unpack(">h", elevData[offset:offset+2])[0]
    if elev != -32768:
        return elev * feetPerMeter
    else:  # missing data - return the gps elevation
        return gpsElev
