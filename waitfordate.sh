#!/bin/bash

# wait for the clock to get set to the present
echo -e "Waiting for correct time\r"
while [ `date +%Y` -le "2000" ]
do
	sleep 1
done

