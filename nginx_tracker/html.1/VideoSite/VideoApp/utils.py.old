# -*- coding: utf-8 -*-

import sys, os, hashlib, StringIO, bencode
from pysqlite2 import dbapi2 as sqlite

_PATH = os.path.abspath(os.path.dirname(__file__))
dirs=_PATH.replace('\\','/').split('/')
pardir = dirs[0]
for di in dirs[1:-1]:
  pardir = pardir+'/'+di 
parpardir = dirs[0]
for di in dirs[1:-2]:
  parpardir = parpardir+'/'+di 


def get_seeders(request, torrent):
    database = os.path.join(parpardir, 'tracker', 'db', 'tracker.db')

    VIDEO_FILES_PATH = os.path.join(pardir, 'files')
    file = os.path.join(VIDEO_FILES_PATH, torrent, torrent+'.torrent')
    torrent_file = open(file, "rb")
    metainfo = bencode.bdecode(torrent_file.read())
    info = metainfo['info']
    hash = hashlib.sha1(bencode.bencode(info)).hexdigest()    

    con = sqlite.connect(database)
    cur = con.cursor()

    binary = hash.decode('hex')
    cur.execute("SELECT * FROM peers WHERE info_hash=(?)", (buffer(binary),) )

    mas = cur.fetchmany(50) 
    addr = [] 
    for row in mas:
      (info_hash, peer_id, compact, ip, port, state, update) = row
      addr.append(ip)
    return addr

