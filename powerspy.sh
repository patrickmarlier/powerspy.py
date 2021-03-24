#!/bin/bash

launchPowerSpy() {

	PS2MAC=$1
	RATE=$2
	OUTPUT_FILE=$3
	powerspy.py -i $RATE $PS2MAC 1> $OUTPUT_FILE 2> err-$OUTPUT_FILE &
	PID=$!
	sleep 10
	if ps -p $PID > /dev/null
	then 
	    echo $PID
	else
	    echo $(launchPowerSpy $PS2MAC $RATE $OUTPUT_FILE)
	fi
}

killPowerSpy() {
	
	PID=$1
	kill -s INT $PID
	sleep 10
}
