#!/bin/bash

echo -e "Starting bluetooth\r"
bluetooth_rfkill_event >/dev/null 2>&1 &
rfkill unblock bluetooth
/usr/local/libexec/bluetooth/bluetoothd &

