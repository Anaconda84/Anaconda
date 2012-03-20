#!/bin/sh

echo "\n$HOME/swarmvideo/SwarmEngine\n" >> $HOME/.profile

PREV_USER=`ls -lA $HOME/.profile | awk '{ print $3 }'`

cd $HOME/swarmvideo
su $PREV_USER ./SwarmEngine &
