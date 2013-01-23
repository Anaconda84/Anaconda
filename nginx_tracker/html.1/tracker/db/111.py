import sqlite3
conn = sqlite3.connect('tracker.db')
c = conn.cursor()

#c.execute("SELECT info_hash FROM peers")
#allentries=c.fetchall()

#print repr(str(allentries[0]))


for row in c.execute("select info_hash from peers"):
    print row[0], str(row[0]).encode('hex')
