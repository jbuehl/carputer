#!/bin/bash

# slow down i2c
echo std > /sys/devices/pci0000:00/0000:00:08.0/i2c_dw_sysnode/mode

# start bluetooth
/root/carputer/bluetooth.sh &

# start the UI
/usr/bin/python /root/ha/haTacoma.py &

# mount the data drive
#/root/carputer/mountdata.sh

# start the GPS service first
/usr/bin/python /root/carputer/gps.py &

# wait for the date to get set from the GPS clock
/root/carputer/waitfordate.sh

# start the rest of the services
/usr/bin/python /root/carputer/diags.py &
/usr/bin/python /root/carputer/9dof.py &

