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

    def instances(self):
      ilist = []
      count = 0
      # build three instances for each node type: on-demand, 1yr, 3yr
      for row in self.data:
        desc =  row['Level']+row['Utilization']+row['Instance Type']
        puc1YR = float(row['Rate 1YR']) / float(row['Rate On-demand'])
        puc3YR = float(row['Rate 3YR']) / float(row['Rate On-demand'])
        
        #TODO: year/time as a constant
        lod = Lease(length = 0, downp = 0, puc = 1)
        l1Y = Lease(length = 8760, downp = float(row['Upfront 1YR']), puc = puc1YR) 
        l3Y = Lease(length = 26280, downp = float(row['Upfront 3YR']), puc = puc3YR) 
        nunit = Unit(capacity = float(row['Compute Units']), time = 1, \
            cost = float(row['Rate On-demand']))

        ilist.append( Instance( name=count, desc=desc+" OD", unit=nunit, 
          lease = lod))
        count += 1
        ilist.append( Instance( name=count, desc=desc+" 1Y", unit=nunit,
          lease = l1Y))
        count += 1
        ilist.append( Instance( name=count, desc=desc+" 3Y", unit=nunit,
          lease = l3Y))
        count += 1
      return ilist

    def dump(self):
      for i in self.data:
        print i
# fin.
