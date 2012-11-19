"""
  Some custom CSV reader/writer helper functions
"""

import csv, codecs, cStringIO
  
class CSVExport:
    """
    A CSV writer which will write rows to CSV file "f",
    """
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.writer = csv.writer(open(f,'wb'), dialect=dialect, **kwds)

    def writerow(self, row):
        self.writer.writerow([s for s in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class CSVImport:
    """
    Read in market configuration data from a CSV file
    """
    def __init__(self, filename):
        self.fd = open(filename, 'rb')
        self.data = csv.DictReader(self.fd)

    def __iter__(self):
       return self


    def dump(self):
      for i in self.data:
        print i
# fin.
