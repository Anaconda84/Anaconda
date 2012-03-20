#!/bin/sh

PREV_USER=`ls -lA -d $HOME | awk '{ print $3 }'`

chown -R $PREV_USER:$PREV_USER $HOME/swarmvideo

cd $HOME/swarmvideo
sudo -b -u $PREV_USER ./SwarmEngine

FLAG=`cat $HOME/.profile | grep SwarmEngine`
if [ -z "$FLAG" ]
then
  echo "\n$HOME/swarmvideo/SwarmEngine" >> $HOME/.profile
fi
