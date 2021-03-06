#!/bin/sh

# Stop IRQ balancer
service irqbalance restart

# Set interface MTU
ifconfig $1 mtu 1500

# Set the scaling governor on each cpu to performance
NUM_CPUS=`grep -c ^processor /proc/cpuinfo`
for i in $(seq 1 `expr $NUM_CPUS - 1`); 
    do 
    echo powersave > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor 
done

