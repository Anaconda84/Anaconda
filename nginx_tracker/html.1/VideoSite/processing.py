# -*- coding: utf-8 -*-

import os
import re
import codecs
import shutil
import subprocess
from settings import *
from pytils import translit

import datetime
import os.path
import sys

import pymktorrent
import pymktorrent.torrent
import pymktorrent.bencode

def processing(str):
  mas = str.split("|")
  str_video = that_coding(translit.translify(mas[10]))
  translit_filename = translit.translify(mas[0])
  translit_filename = translit_filename.replace(' ','_')
  ##### codding video ###########################
#  command = 'start /WAIT /HIGH codding.bat \"'+str_video+'\" '+translit_filename+'.webm'
#  print command
#  run(command)
  #############################################3
  make_torrent(translit_filename+'.webm', translit_filename+'.torrent')
  if not os.path.isdir(VIDEO_TORRENT):
    os.makedirs(VIDEO_TORRENT)
  if not os.path.isdir(VIDEO_TORRENT+'/'+translit_filename):
    os.makedirs(VIDEO_TORRENT+'/'+translit_filename)
  shutil.copy(translit_filename+'.torrent',VIDEO_TORRENT+'/'+translit_filename+'/'+translit_filename+'.torrent')
  shutil.move(translit_filename+'.webm',VIDEO_TORRENT+'/'+translit_filename+'/'+translit_filename+'.webm')
  if not os.path.isdir(OUTDIR):
    os.makedirs(OUTDIR)
  if not os.path.isdir(OUTDIR+'/Torrents/'):
    os.makedirs(OUTDIR+'/Torrents/')
  shutil.move(translit_filename+'.torrent',OUTDIR+'/Torrents/'+translit_filename+'.torrent')

  command = deluge+' \"add -p '+VIDEO_TORRENT+'/'+translit_filename+' '+VIDEO_TORRENT+'/'+translit_filename+'/'+translit_filename+'.torrent\"'
#  run(command)
  if os.path.exists(VIDEO_TORRENT+'/'+translit_filename+'/'+translit_filename+'.webm') and os.path.exists(VIDEO_TORRENT+'/'+translit_filename+'/'+translit_filename+'.torrent'):
    output_file(mas, translit_filename+'.torrent')


def that_coding(path):
  if os.path.exists(path):
    if os.path.isfile(path):  
      pass
    else:
      dict = piecelist(path)
      chapter = recognize_film(dict)
      lstfile = dict[chapter]
      del lstfile[0]
      strout = ''
      for file in lstfile:
        strout = strout + file + '|'
      return strout

def piecelist(path):
  strout = ''
  path = path+'\\VIDEO_TS'
  group_files = {}
  for i in os.listdir(path):
    file = path+'\\'+i
    if os.path.isfile(file):
      result = re.finditer( ur"VTS_(\d+)_(\d+)\.VOB", os.path.basename(file) )
      for match in result:
	if group_files.has_key(match.groups()[0]):
	  lst = group_files.get(match.groups()[0])
          lst.append(file)
	else:
	  lst = []
	  lst.append(file)

	group_files[match.groups()[0]] = lst
	
  return group_files

def recognize_film(dict):
  out = {}
  out_sort_lst = []
  for chapter in dict.keys():
    list_file = dict[chapter]
    allsize = 0
    for file in list_file:
      size = os.path.getsize(file)
      allsize = allsize + size
    out[allsize] = chapter

  for key in sorted(out):
    out_sort_lst.append(out[key])
#  print out_sort_lst
  return out_sort_lst[-1]

def output_file(mas, torrent):
  dt = datetime.datetime.now() 
  date_time = dt.strftime('%Y_%m_%d_%H_%M_%S')
  strout = mas[0]+'|'+mas[1]+'|'+mas[2]+'|'+mas[3]+'|'+mas[4]+'|'+mas[5]+'|'+mas[6]+'|'+mas[7]+'|'+date_time+'|'+mas[8]+'|'+mas[9]+'|'+URL+'|'+torrent
  # write to output file
  if not os.path.isdir(OUTDIR):
    os.makedirs(OUTDIR)
  fileout = OUTDIR+'/'+OUTFILE
  output = open(fileout, 'a')
  output.write(strout.encode('utf8')+"\n")
  output.close()
  # copy poster
  (root, ext) = os.path.splitext(mas[9])
  if not os.path.isdir(OUTDIR+'/Image/'):
    os.makedirs(OUTDIR+'/Image/')
  dstfile = translit.translify(mas[0]).replace(r'.','')+ext
  dstfile = dstfile.replace(' ','_')
  print dstfile
  shutil.copy(mas[9],OUTDIR+'/Image/'+dstfile)
  
def make_torrent(source, destination):
  run('mktorrent.exe -a '+announce+' -o '+destination+' '+source)

def run(command):
  pipe1,pipe2,pipe3=os.popen3(command)
  retout=pipe2.read()
  reterr=pipe3.read()
  print retout
  print reterr
  pipe1.close()
  pipe2.close()
  pipe3.close()

if __name__ == '__main__':
  for i in os.listdir(BUFFER):
    file = BUFFER+'\\'+i
    if os.path.isfile(file):
      infile = codecs.open(file, encoding='utf-8')
      str = infile.readline()
      str = re.sub("\r\n", '', str)
      processing(str)
      infile.close()

