# -*- coding: utf-8 -*-
import sqlite3
import os
import shutil
from urlparse import urlparse

source = 'c:/Tmp/OUTPUT'
inputfile = 'output.log'
dest = 'files'
video_url = 'http://107.22.233.233:8000/video.html'
static_url = 'http://107.22.233.233:8000'

conn=sqlite3.connect('videobaza.db')
c = conn.cursor()

input = open(source+'/'+inputfile, 'r')
text = input.read()
lststr = text.split("\n")
for line in lststr:
  line = line.decode('utf8')
  mas = line.split('|')
  if len(mas) == 13:
    # ����������� ������ poster, torrent
    (dir, ext) = os.path.splitext(mas[12])
    if not os.path.isdir(dest):
      os.makedirs(dest)
    if not os.path.isdir(dest):
      os.makedirs(dest)
    if not os.path.isdir(dest+'/'+dir):
      os.makedirs(dest+'/'+dir)
    for file in os.listdir(source+'/'+dir):
      shutil.copy(source+'/'+dir+'/'+file,dest+'/'+dir)
    shutil.rmtree(source+'/'+dir)

    if os.path.exists(dest+'/'+dir+'/'+dir+'.torrent'):
      o = urlparse(mas[11])
      mas1 = []
      mas1.append(None)
      mas1.append(mas[0])
      mas1.append(mas[1])
      mas1.append(mas[2])
      mas1.append(mas[3])
      mas1.append(mas[4])
      mas1.append(mas[5]+':'+mas[6])
      mas1.append(mas[7])
      mas1.append(mas[8])
      mas1.append(mas[9])
      mas1.append(static_url+'/'+dir+'/'+mas[10])
      mas1.append(video_url)
      mas1.append(static_url+'/'+dir+'/'+mas[12])
      in_baza = tuple(mas1)
      #print in_baza

      try:
        # ������� ���� ������
        c.execute("""insert into VideoApp_videobaza values (?,?,?,?,?,?,?,?,?,?,?,?,?)""", in_baza)
      except:
        print 'Cant insert: ',in_baza,'\n'

input.close()

# ���������� (commit) ���������
conn.commit()
# �������� �������, � ������ ���� �� ������ �� �����
c.close() 

os.remove(source+'/'+inputfile)


