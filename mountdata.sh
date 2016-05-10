#!/bin/bash

# wait for the usb bus to come up
echo -e "Waiting for USB\r"
while [ ! -e "/dev/sda1" ]
do
#	echo "Waiting for usb"
	sleep 1
done

# mount the data drive
echo -e "Mounting data\r"
mount /dev/sda1 /root/data
