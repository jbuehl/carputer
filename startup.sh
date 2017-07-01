#!/bin/bash -

# set the system time from the RTC module
echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
sleep 1
hwclock -s

# turn off wifi to prevent audio skipping
#/root/carputer/wifi.sh off &

# fork the process to connect to trusted devices
#/root/carputer/btconnect.sh

