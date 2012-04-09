#!/bin/sh

VERSION="0.8"
DIST="SwarmVideo.linux-$VERSION.tar.gz"

rm -R build
rm -R dist

python setup_linux_pkg.py build

mkdir dist
cp LICENSE.txt dist
cp README.linux dist
cd build/exe.linux-i686-2.7
tar -cvzf $DIST *
mv $DIST ../../dist


#HOME="/root"
#cd /usr/bin/swarmvideo
#./SwarmEngine &

#FLAG=`cat /etc/profile | grep SwarmEngine`
#if [ -z "$FLAG" ]
#then
#  echo "/usr/bin/swarmvideo/SwarmEngine" >> /etc/profile
#fi
