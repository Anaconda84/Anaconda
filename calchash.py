import hashlib
import os

# Calculate hash files in directory for update site
dir = '.'
out = 'hashlist.log'

def hash(filename):
   fd = open(filename, 'r')
   h = hashlib.new('sha256')
   h.update(fd.read())
   result = h.hexdigest()
   return result

def walk(dir):
  for name in os.listdir(dir):
    path = os.path.join(dir, name)
    if os.path.isfile(path):
        fd_out.write(path+"\t"+hash(path)+"\n")
        print path+"\t"+hash(path)
    else:
        walk(path)

fd_out = open(out, 'w')
walk(dir)
fd_out.close()


