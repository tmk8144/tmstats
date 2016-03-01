#!/usr/bin/python
""" Update the grouped.csv file with current information from the database.  Does NOT change 'newarea'!
"""

import dbconn, tmutil, sys, os, csv, datetime

clubs = {} 

class myclub:
    
    fields = ['clubnumber', 'clubname', 'latitude', 'longitude', 'place', 'address', 'city', 'state', 'zip', 'country', 'area', 'division', 'meetingday', 'meetingtime', 'color', 'goalsmet', 'activemembers']
    
    outfields = ['clubnumber', 'clubname', 'oldarea', 'newarea', 'color', 'goalsmet', 'activemembers', 'meetingday', 'meetingtime', 'place', 'address', 'city', 'state', 'zip', 'country',  'latitude', 'longitude', ]
    
    def __init__(self, *args):
        # Assign values
        for (f, v) in zip(self.fields, args):
            self.__dict__[f] = v
        # Fix up clubnumber
        self.clubnumber = '%s' % self.clubnumber
        self.distances = []
        self.oldarea = self.division + self.area
        clubs[self.clubnumber] = self
        if self.latitude == 0.0 or self.longitude == 0.0:
            print self.clubname, self.clubnumber, 'has no location assigned.'
            
    def out(self):
        return ['%s' % self.__dict__[f] for f in self.outfields]
        
def inform(*args, **kwargs):
    """ Print information to 'file' unless suppressed by the -quiet option.
          suppress is the minimum number of 'quiet's that need be specified for
          this message NOT to be printed. """
    suppress = kwargs.get('suppress', 1)
    file = kwargs.get('file', sys.stderr)
    
    if parms.quiet < suppress:
        print >> file, ' '.join(args)

### Insert classes and functions here.  The main program begins in the "if" statement below.

if __name__ == "__main__":
 
    import tmparms
    from tmutil import gotodatadir
    # Make it easy to run under TextMate
    gotodatadir()
        
    reload(sys).setdefaultencoding('utf8')
    
    # Handle parameters
    parms = tmparms.tmparms()
    parms.add_argument('--quiet', '-q', action='count')
    parms.add_argument('--mapoverride', dest='mapoverride', default=None, help='Google spreadsheet with overriding address and coordinate information')
    parms.add_argument('--file', dest='file', default='d101align.csv')
    # Add other parameters here
    parms.parse() 
   
    # Connect to the database        
    conn = dbconn.dbconn(parms.dbhost, parms.dbuser, parms.dbpass, parms.dbname)
    curs = conn.cursor()
    
    # Get data from clubs
    curs.execute('SELECT MAX(lastdate) FROM CLUBS')
    lastdate = curs.fetchone()[0]
    whereclause = 'WHERE c.division IN ("A", "B", "F", "G", "J") AND c.city NOT LIKE "%%Palo Alto%%" AND c.lastdate = "%s"' % lastdate
    c2 = conn.cursor()
    curs.execute('SELECT g.clubnumber, g.clubname, g.latitude, g.longitude, g.place, g.address, g.city, g.state, g.zip, g.country, c.area, c.division, c.meetingday, c.meetingtime FROM geo g INNER JOIN clubs c on g.clubnumber = c.clubnumber ' + whereclause)
    for row in curs.fetchall():
        c2.execute('SELECT color, goalsmet, activemembers FROM clubperf WHERE entrytype = "L" AND clubnumber = %s', (row[0],))
        row = [cell for cell in row] + [cell for cell in c2.fetchone()]
        myclub(*row)
        
        
    # Now, get the performance metrics of interest

        
    # If there are overrides to club positioning, handle them now
    if parms.mapoverride:
        overrideClubPositions(clubs, parms.mapoverride, parms.googlemapsapikey)
        

            
    # Now, get the 'newarea' information from the old file.
    infile = open(parms.file, 'rbU')
    reader = csv.DictReader(infile)
    for row in reader:
        try:
            clubs[row['clubnumber']].newarea = row['newarea']
        except KeyError:
            print row['clubnumber'], 'not found'
    infile.close()
    os.rename(parms.file, datetime.datetime.today().strftime('%Y-%m-%d') + '.' + 
parms.file)
    # And write out the results
    outfile = open(parms.file, 'wb')
    writer = csv.writer(outfile)
    writer.writerow(myclub.outfields)
    # Sort the clubs by newarea and clubnumber
    outclubs = sorted(clubs.values(), key=lambda c:'%s %9s' % (c.newarea, c.clubnumber))
    for c in outclubs:
        writer.writerow(c.out())
    outfile.close()
    
    
