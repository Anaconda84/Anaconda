#!/bin/sh

HOME="/root"
cd /usr/bin/swarmvideo
./SwarmEngine &

FLAG=`cat /etc/profile | grep SwarmEngine`
if [ -z "$FLAG" ]
then
  echo "/usr/bin/swarmvideo/SwarmEngine" >> /etc/profile
fi
