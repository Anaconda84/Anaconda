#!/usr/bin/env python
#-*- coding:utf-8 -*-
import os

from glob import glob
from py2deb import Py2deb

p=Py2deb("swarmvideo")

p.author="Anaconda84"
p.mail="kos.shilow@gmail.com"
p.description="Proxy server for playing torrent video."
p.url = "http://secret.com"
p.depends="python-wxgtk2.8"
p.license="gpl"
p.section="utils"
p.arch="all"
p.postinstall="postinstall.sh"
#p.preinstall="preinstall.sh"

dir = '.'

filelist = []
for root, dirs, files in os.walk(dir):
    for name in files:
        fullname = os.path.join(root, name)
        filelist.append(fullname)

home = os.path.expanduser('~')
p[home+"/swarmvideo"] = filelist

p.generate("0.8")

