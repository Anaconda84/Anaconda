import os
dir='c:\kos\kos1\kos2'
dirs=dir.replace('\\','/').split('/')
pardir = dirs[0]
for di in dirs[1:-1]:
  pardir = pardir+'/'+di 

print pardir